# -*- coding: UTF-8 -*-
"""
Database utilities.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from collections import namedtuple
from datetime import datetime

from sqlalchemy import desc

from yokadi.core import db
from yokadi.core.db import Task, NOTE_KEYWORD
from yokadi.core.yokadiexception import YokadiException
from yokadi.core import dbutils
from yokadi.core.dbutils import KeywordFilter
from yokadi.ycli import parseutils


MEditEntry = namedtuple("MEditEntry", ["id", "status", "title", "keywords"])


def createMEditText(entries):
    def formatLine(entry):
        status = entry.status[0].upper()
        line = parseutils.createLine(None, entry.title, entry.keywords)
        return "%d %s %s" % (entry.id, status, line)

    lines = [formatLine(x) for x in entries]
    return "\n".join(lines)


def parseMEditText(text):
    def createException(message):
        return YokadiException("Error line %d (\"%s\"): %s" % (num + 1, line, message))

    lst = []
    for num, line in enumerate(text.split("\n")):
        line = line.strip()
        if not line or line[0] == "#":
            continue
        tokens = line.split(" ", 2)
        nbTokens = len(tokens)
        if nbTokens < 3:
            if nbTokens == 2 and tokens[0] == "-":
                # Special case: adding a one-word new task
                tokens.append("")
            else:
                raise createException("Invalid line")

        if tokens[0] == "-":
            id = None
        else:
            try:
                id = int(tokens[0])
            except ValueError:
                raise createException("Invalid id value")

        statusChar = tokens[1].lower()
        line = tokens[2]
        if statusChar == "n":
            status = "new"
        elif statusChar == "s":
            status = "started"
        elif statusChar == "d":
            status = "done"
        elif id == None:
            # Special case: if this is a new task, then statusChar is actually a
            # one-letter word starting the task title
            status = "new"
            line = tokens[1] + ((" " + line) if line else "")
        else:
            raise createException("Invalid status")

        _, title, keywords = parseutils.parseLine("dummy " + line)

        lst.append(MEditEntry(id, status, title, keywords))
    return lst


def createMEditEntriesForProject(project):
    session = db.getSession()
    lst = session.query(Task).filter(Task.projectId == project.id,
                                     Task.status != 'done')

    lst = KeywordFilter(NOTE_KEYWORD, negative=True).apply(lst)
    lst = lst.order_by(desc(Task.urgency))
    return [createMEditEntryForTask(x) for x in lst]


def createMEditEntryForTask(task):
    return MEditEntry(task.id, task.status, task.title, task.getKeywordDict())


def applyMEditChanges(project, oldList, newList, interactive=True):
    """
    Modify a project so that its task list is newList

    @param project: the project name
    @param oldList: a list of Task instances
    @param newList: a list of MEditEntry
    @param interactive: whether to confirm creation of new keywords
    """
    session = db.getSession()

    # Sanity check: all ids in newList should be in oldList
    oldIds = set([x.id for x in oldList])
    newIds = set([x.id for x in newList if x.id is not None])
    unknownIds = newIds.difference(oldIds)
    if unknownIds:
        idString = ", ".join([str(x) for x in unknownIds])
        raise YokadiException("Unknown id(s): %s" % idString)

    # Check keywords
    for entry in newList:
        for name in entry.keywords:
            dbutils.getOrCreateKeyword(name, interactive=interactive)

    # Remove tasks whose lines have been deleted
    for id in oldIds.difference(newIds):
        task = dbutils.getTaskFromId(id)
        session.delete(task)

    # Update existing tasks, add new ones
    nbTasks = len(newList)
    for pos, newEntry in enumerate(newList):
        if newEntry.id:
            task = dbutils.getTaskFromId(newEntry.id)
        else:
            task = Task(creationDate=datetime.now().replace(second=0, microsecond=0), project=project)
        task.title = newEntry.title
        task.setKeywordDict(newEntry.keywords)
        task.setStatus(newEntry.status)
        task.urgency = nbTasks - pos
        if newEntry.id:
            session.merge(task)
        else:
            session.add(task)


# vi: ts=4 sw=4 et
