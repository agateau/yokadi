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


DOC_COMMENT = """
Line format: <id> <status> <task title>

To change the title of a task, just change the text after the status character.
You can add or remove keywords like you do when using t_add.

To change the status of a task, change the status character to one of:
 N new
 S started
 D done

To add a new task, add a new line using '-' for the task id. If you do not
specify a status, the task will be marked as new. Examples:

- This is a new task
- N This is another new task
- S This task has already been started

To adjust task urgencies, re-order the lines.

To remove a task, delete its line or comment it out with '#'.

To cancel changes, quit without saving.

Empty lines and lines starting with a '#' are ignored.

Warning: Do NOT edit the task id, this will confuse Yokadi.
"""


class ParseError(YokadiException):
    def __init__(self, message, lineNumber, line):
        fullMessage = "Error line %d (\"%s\"): %s" % (lineNumber + 1, line, message)
        YokadiException.__init__(self, fullMessage)
        self.lineNumber = lineNumber
        self.message = message


def createMEditText(entries, docComment=DOC_COMMENT):
    def formatLine(entry):
        status = entry.status[0].upper()
        line = parseutils.createLine(None, entry.title, entry.keywords)
        return "%d %s %s" % (entry.id, status, line)

    def prefixComment(comment):
        for line in comment.strip().splitlines():
            if line:
                yield "# " + line
            else:
                yield "#"

    lines = [formatLine(x) for x in entries]
    lines.append('')
    lines.extend(prefixComment(docComment))
    return "\n".join(lines) + "\n"


def parseMEditLine(line):
    tokens = line.split(" ", 2)
    nbTokens = len(tokens)
    if nbTokens < 3:
        if nbTokens == 2 and tokens[0] == "-":
            # Special case: adding a one-word new task
            tokens.append("")
        else:
            raise Exception("Invalid line")

    if tokens[0] == "-":
        id = None
    else:
        try:
            id = int(tokens[0])
        except ValueError:
            raise Exception("Invalid id value")

    statusChar = tokens[1].lower()
    line = tokens[2]
    if statusChar == "n":
        status = "new"
    elif statusChar == "s":
        status = "started"
    elif statusChar == "d":
        status = "done"
    elif id is None:
        # Special case: if this is a new task, then statusChar is actually a
        # one-letter word starting the task title
        status = "new"
        line = tokens[1] + ((" " + line) if line else "")
    else:
        raise Exception("Invalid status")

    _, title, keywords = parseutils.parseLine("dummy " + line)
    return MEditEntry(id, status, title, keywords)


def parseMEditText(text):
    lst = []
    ids = set()
    for num, line in enumerate(text.split("\n")):
        line = line.strip()
        if not line or line[0] == "#":
            continue

        try:
            entry = parseMEditLine(line)
        except Exception as exc:
            exc = ParseError(str(exc), lineNumber=num + 1, line=line)
            raise exc

        if entry.id is not None:
            if entry.id in ids:
                exc = ParseError("Duplicate id value", lineNumber=num + 1, line=line)
                raise exc
            ids.add(entry.id)

        lst.append(entry)
    return lst


def createEntriesForProject(project):
    session = db.getSession()
    lst = session.query(Task).filter(Task.projectId == project.id,
                                     Task.status != 'done')

    lst = KeywordFilter(NOTE_KEYWORD, negative=True).apply(lst)
    lst = lst.order_by(desc(Task.urgency))
    return [createEntryForTask(x) for x in lst]


def createEntryForTask(task):
    return MEditEntry(task.id, task.status, task.title, task.getKeywordDict())


def applyChanges(project, oldList, newList, interactive=True):
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
            session.add(task)
        task.title = newEntry.title
        task.setKeywordDict(newEntry.keywords)
        task.setStatus(newEntry.status)
        task.urgency = nbTasks - pos


# vi: ts=4 sw=4 et
