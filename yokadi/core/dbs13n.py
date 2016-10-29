# dbs13n: Database Serialization
from datetime import datetime

import dateutil.parser

from yokadi.core import dbutils
from yokadi.core.db import Project
from yokadi.core.recurrencerule import RecurrenceRule

TASK_DATE_FIELDS = {"creationDate", "dueDate", "doneDate"}


def _dictFromRow(row, skippedKeys=None):
    if skippedKeys is None:
        skippedKeys = set()
    dct = dict()
    for key, value in row.__dict__.items():
        if key in skippedKeys or key == "id" or key.startswith("_sa_"):
            continue
        if isinstance(value, datetime):
            value = value.isoformat()
        dct[key] = value
    return dct


def _updateRowFromDict(session, row, dct, skippedKeys=None):
    if skippedKeys is None:
        skippedKeys = set()
    for key, value in dct.items():
        if key in skippedKeys:
            continue
        setattr(row, key, value)
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
    return _dictFromRow(project, skippedKeys={"tasks"})


def updateProjectFromDict(session, project, dct):
    _updateRowFromDict(session, project, dct)


def dictFromTask(task):
    dct = _dictFromRow(task, skippedKeys={"recurrence", "project", "projectId", "taskKeywords"})
    dct["projectUuid"] = task.project.uuid
    dct["keywords"] = task.getKeywordDict()
    dct["recurrence"] = task.recurrence.toDict()
    return dct


def updateTaskFromDict(session, task, dct):
    projectUuid = dct.pop("projectUuid")
    project = session.query(Project).filter_by(uuid=projectUuid).one()
    dct["project"] = project

    _convertStringsToDates(dct, TASK_DATE_FIELDS)
    _updateRowFromDict(session, task, dct, skippedKeys={"recurrence", "keywords"})
    keywords = dct["keywords"]
    dbutils.createMissingKeywords(keywords.keys(), interactive=False)
    task.setKeywordDict(keywords)
    # FIXME: dct.get("recurrence", {}) can be replaced with a dct["recurrence"]
    # when all DBs of early adopters have been updated
    task.recurrence = RecurrenceRule.fromDict(dct.get("recurrence", {}))


def dictFromAlias(alias):
    return _dictFromRow(alias)


def updateAliasFromDict(session, alias, dct):
    _updateRowFromDict(session, alias, dct)
