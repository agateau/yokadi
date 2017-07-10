"""
dbs13n: Database Serialization

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from datetime import datetime

import dateutil.parser

from yokadi.core import dbutils
from yokadi.core.db import Project
from yokadi.core.recurrencerule import RecurrenceRule

TASK_DATE_FIELDS = {"creation_date", "due_date", "done_date"}


_PROJECT_KEYS = (
    ("uuid", "uuid"),
    ("name", "name"),
    ("active", "active"),
)

_TASK_KEYS = (
    ("uuid", "uuid"),
    ("title", "title"),
    ("creationDate", "creation_date"),
    ("dueDate", "due_date"),
    ("doneDate", "done_date"),
    ("description", "description"),
    ("urgency", "urgency"),
    ("status", "status"),
)

_ALIAS_KEYS = (
    ("uuid", "uuid"),
    ("name", "name"),
    ("command", "command"),
)


def _dictFromRow(row, keyList):
    dct = dict()
    for rowKey, jsonKey in keyList:
        value = getattr(row, rowKey)
        if isinstance(value, datetime):
            value = value.isoformat()
        dct[jsonKey] = value
    return dct


def _updateRowFromDict(session, row, dct, keyList):
    for rowKey, jsonKey in keyList:
        setattr(row, rowKey, dct[jsonKey])
    session.add(row)


def _convertStringsToDates(dct, keys):
    for key in keys:
        try:
            value = dct[key]
        except KeyError:
            continue
        if value is None:
            continue
        dct[key] = dateutil.parser.parse(value)


def dictFromProject(project):
    return _dictFromRow(project, _PROJECT_KEYS)


def updateProjectFromDict(session, project, dct):
    _updateRowFromDict(session, project, dct, _PROJECT_KEYS)


def dictFromTask(task):
    dct = _dictFromRow(task, _TASK_KEYS)
    dct["project_uuid"] = task.project.uuid
    dct["keywords"] = task.getKeywordDict()
    dct["recurrence"] = task.recurrence.toDict()
    return dct


def updateTaskFromDict(session, task, dct):
    projectUuid = dct["project_uuid"]
    # Set project *before* calling _updateRowFromDict because it calls session.add
    task.project = session.query(Project).filter_by(uuid=projectUuid).one()

    _convertStringsToDates(dct, TASK_DATE_FIELDS)
    _updateRowFromDict(session, task, dct, _TASK_KEYS)

    keywords = dct["keywords"]
    dbutils.createMissingKeywords(keywords.keys(), interactive=False)
    task.setKeywordDict(keywords)
    # FIXME: dct.get("recurrence", {}) can be replaced with a dct["recurrence"]
    # when all DBs of early adopters have been updated
    task.recurrence = RecurrenceRule.fromDict(dct.get("recurrence", {}))


def dictFromAlias(alias):
    return _dictFromRow(alias, _ALIAS_KEYS)


def updateAliasFromDict(session, alias, dct):
    _updateRowFromDict(session, alias, dct, _ALIAS_KEYS)
