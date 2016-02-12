# dbs13n: Database Serialization
from datetime import datetime

import dateutil.parser

from yokadi.core import dbutils

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


def _updateRowFromDict(row, dct, skippedKeys=None):
    if skippedKeys is None:
        skippedKeys = set()
    for key, value in dct.items():
        if key in skippedKeys:
            continue
        setattr(row, key, value)


def _convertStringsToDates(dct, keys):
    for key in keys:
        try:
            value = dct[key]
        except KeyError:
            continue
        if value is None:
            continue
        dct[key] = dateutil.parser.parse(value)


def dictFromTask(task):
    dct = _dictFromRow(task, skippedKeys={"recurrenceId", "projectId", "taskKeywords"})
    dct["project"] = task.project.name
    dct["keywords"] = task.getKeywordDict()
    # TODO: recurrence
    return dct


def updateTaskFromDict(task, dct):
    projectName = dct.pop("project")
    project = dbutils.getOrCreateProject(projectName, interactive=False)
    dct["project"] = project

    _convertStringsToDates(dct, TASK_DATE_FIELDS)
    _updateRowFromDict(task, dct, skippedKeys={"recurrence", "keywords"})
    keywords = dct["keywords"]
    dbutils.createMissingKeywords(keywords.keys(), interactive=False)
    task.setKeywordDict(keywords)
    # TODO: recurrence
