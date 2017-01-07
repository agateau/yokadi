# -*- coding: UTF-8 -*-
"""
Implementation of completers for various Yokadi objects.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from yokadi.ycli.basicparseutils import parseParameters, simplifySpaces
from yokadi.core import db
from yokadi.core.db import Config, Keyword, Project, Task
from yokadi.core.ydateutils import WEEKDAYS
from yokadi.core.recurrencerule import FREQUENCIES


def computeCompleteParameterPosition(text, line, begidx, endidx):
    before = simplifySpaces(line[:begidx].strip())
    return before.count(" ") + 1


def getItemPropertiesStartingWith(item, field, text):
    """Return a list of item.field starting with text
    @param item: the object item, example : Task, Project, Keyword...
    @param field: the item's field lookup : Project.q.name, Task.q.title, Keyword.q.name. Don't forget the magic q
    @param text: The begining of the text as a str
    @return: list of matching strings"""
    session = db.getSession()
    return [x.name for x in session.query(item).filter(field.like(str(text) + "%"))]


class ProjectCompleter(object):
    def __init__(self, position):
        self.position = position

    def __call__(self, text, line, begidx, endidx):
        if computeCompleteParameterPosition(text, line, begidx, endidx) == self.position:
            return ["%s " % x for x in getItemPropertiesStartingWith(Project, Project.name, text)]
        else:
            return []


class KeywordCompleter(object):
    def __init__(self, position):
        self.position = position

    def __call__(self, text, line, begidx, endidx):
        if computeCompleteParameterPosition(text, line, begidx, endidx) == self.position:
            return getItemPropertiesStartingWith(Keyword, Keyword.name, text)
        else:
            return []


class MultiCompleter(object):
    """A completer which takes multiple completers and apply them in turn,
    according to their position"""
    def __init__(self, *completers):
        self.completers = completers

    def __call__(self, text, line, begidx, endidx):
        for completer in self.completers:
            lst = completer(text, line, begidx, endidx)
            if lst:
                return lst
        else:
            return []


def projectAndKeywordCompleter(cmd, text, line, begidx, endidx, shift=0):
    """@param shift: argument position shift. Used when command is omitted (t_edit usecase)"""
    position = computeCompleteParameterPosition(text, line, begidx, endidx)
    position -= len(parseParameters(line)[0])  # remove arguments from position count
    position += shift  # Apply argument shift
    if position == 1:  # Projects
        return ["%s" % x for x in getItemPropertiesStartingWith(Project, Project.name, text)]
    elif position >= 2 and line[-1] != " " and line.split()[-1][0] == "@":  # Keywords (we ensure that it starts with @
        return ["%s" % x for x in getItemPropertiesStartingWith(Keyword, Keyword.name, text)]


def confCompleter(cmd, text, line, begidx, endidx):
    return getItemPropertiesStartingWith(Config, Config.name, text)


def taskIdCompleter(cmd, text, line, begidx, endidx):
    # TODO: filter on parameter position
    # TODO: potential performance issue with lots of tasks, find a better way to do it
    session = db.getSession()
    tasks = [x for x in session.query(Task).filter(Task.status != 'done') if str(x.id).startswith(text)]
    print()
    for task in tasks:
        # Move that in a renderer class ?
        print("%s: %s / %s" % (task.id, task.project.name, task.title))
    return [str(x.id) for x in tasks]


def recurrenceCompleter(cmd, text, line, begidx, endidx):
    frequencies = [x.lower() for x in FREQUENCIES.values()] + ["none"]
    weekdays = [x.lower() for x in WEEKDAYS.keys()]

    position = computeCompleteParameterPosition(text, line, begidx, endidx)
    if position == 1:  # Task id
        return taskIdCompleter(cmd, text, line, begidx, endidx)
    elif position == 2:  # frequency
        return [x for x in frequencies if x.startswith(text.lower())]
    elif position == 3 and "weekly" in line.lower():
        return [x for x in weekdays if x.startswith(text.lower())]


def dueDateCompleter(cmd, text, line, begidx, endidx):
    position = computeCompleteParameterPosition(text, line, begidx, endidx)
    if position == 1:  # Task id
        return taskIdCompleter(cmd, text, line, begidx, endidx)
    elif position == 2 and not text.startswith("+"):  # week day
        return [str(x) for x in list(WEEKDAYS.keys()) if str(x).lower().startswith(text.lower())]

# vi: ts=4 sw=4 et
