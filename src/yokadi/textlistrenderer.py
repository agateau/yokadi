# -*- coding: UTF-8 -*-
"""
Text rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPLv3
"""
from datetime import datetime

import colors as C
import dateutils
from db import Config, Task
import tui


def colorizer(value, reverse=False):
    """Return a color according to value.
    @param value: value used to determine color. Low (0) value means not urgent/visible, high (100) value means important
    @param reverse: If false low value means important and vice versa
    @return: a color code or None for no color"""
    if reverse:
        value = 100 - value
    if value > 75:
        return C.RED
    elif value > 50:
        return C.PURPLE
    elif value > 25:
        return C.ORANGE
    else:
        return None


class Column(object):
    __slots__ = ["title", "width", "formater"]

    def __init__(self, title, width, formater):
        """
        formater is a callable which accepts a task and returns a tuple
        of the form (string, color)
        color may be None if no color should be applied
        """
        self.title = title
        self.width = width
        self.formater = formater


    def createHeader(self):
        return self.title.ljust(self.width)


    def createCell(self, task):
        value, color = self.formater(task)

        if color:
            cell = color
        else:
            cell = ""
        cell = cell + value.ljust(self.width)
        if color:
            cell = cell + C.RESET
        return cell


def idFormater(task):
    return str(task.id), None

class TitleFormater(object):
    def __init__(self, width):
        self.width = width

    def __call__(self, task):
        keywords = [k for k in task.getKeywordDict().keys() if not k.startswith("_")]
        if keywords:
            keywords = C.BOLD+", ".join(keywords)+C.RESET
            title = "%s (%s)" % (task.title, keywords)
            titleWidth = len(title) - len(C.BOLD) - len(C.RESET)
        else:
            title = task.title
            titleWidth = len(title)

        hasDescription = task.description != ""
        maxLength = self.width
        if hasDescription:
            maxLength -= 1
        if titleWidth > maxLength:
            title = title[:maxLength - 1] + ">"
        else:
            if keywords:
                title = title.ljust(maxLength + len(C.BOLD) + len(C.RESET))
            else:
                title = title.ljust(maxLength)
        if hasDescription:
            title = title + "*"

        return title, None

def urgencyFormater(task):
    return str(task.urgency), colorizer(task.urgency)

def statusFormater(task):
    if task.status == "started":
        color = C.BOLD
    else:
        color = None
    return task.status[0].upper(), color

class AgeFormater(object):
    def __init__(self, today):
        self.today = today

    def __call__(self, task):
        delta = self.today - task.creationDate
        return dateutils.formatTimeDelta(delta), colorizer(delta.days)

class DueDateFormater(object):
    def __init__(self, today, shortFormat):
        self.today = today
        self.shortFormat = shortFormat

    def __call__(self, task):
        if not task.dueDate:
            return "", None
        delta = task.dueDate - self.today
        if delta.days != 0:
            value = task.dueDate.strftime("%x %H:%M")
        else:
            value = task.dueDate.strftime("%H:%M")

        if self.shortFormat:
            value = dateutils.formatTimeDelta(delta)
        else:
            value = value + " (%s)" % dateutils.formatTimeDelta(delta)

        color = colorizer(delta.days * 33, reverse=True)
        return value, color


class TextListRenderer(object):
    def __init__(self, out):
        self.out = out
        self._taskList = []
        self._maxTitleWidth = 0
        self.today = datetime.today().replace(microsecond=0)


    def addTaskList(self, sectionName, taskList):
        """Store tasks for this section
        @param sectionName: name of the task groupement section
        @type sectionName: unicode
        @param taskList: list of tasks to display
        @type taskList: list of db.Task instances
        """
        self._taskList.append((sectionName, taskList))
        # Find max title width
        for task in taskList:
            self._maxTitleWidth = max(self._maxTitleWidth, len(task.title))
        # Keep some space for potential '*' suffix
        self._maxTitleWidth += 1

    def end(self):
        termWidth = tui.getTermWidth()
        idWidth = max(2, len(str(Task.select().max(Task.q.id))))
        titleWidth = self._maxTitleWidth
        if termWidth < 100:
            dueDateWidth = 8
            shortDateFormat = True
        else:
            dueDateWidth = 26
            shortDateFormat = False
        self.columns = [
            Column("ID"       , idWidth     , idFormater),
            Column("Title"    , titleWidth  , TitleFormater(titleWidth)),
            Column("U"        , 3           , urgencyFormater),
            Column("S"        , 1           , statusFormater),
            Column("Age"      , 8           , AgeFormater(self.today)),
            Column("Due date" , dueDateWidth, DueDateFormater(self.today, shortDateFormat))
            ]

        # If table is larger than terminal, reduce width of title column
        totalWidth = sum([x.width for x in self.columns])
        if totalWidth > termWidth:
            titleWidth -= (totalWidth - termWidth) + len(self.columns)
            for column in self.columns:
                if column.title == "Title":
                    column.width = titleWidth
                    column.formater = TitleFormater(titleWidth)

        # Print table
        for sectionName, taskList in self._taskList:
            self._renderTaskListHeader(sectionName)
            for task in taskList:
                self._renderTaskListRow(task)


    def _renderTaskListHeader(self, sectionName):
        """
        @param sectionName: name used for list header
        @type sectionName: unicode"""

        cells = [x.createHeader() for x in self.columns]
        line = "|".join(cells)
        width = len(line)
        print >>self.out
        print >>self.out, C.CYAN + sectionName.center(width) + C.RESET
        print >>self.out, C.BOLD + line + C.RESET
        print >>self.out, "-" * width


    def _renderTaskListRow(self, task):
        cells = [column.createCell(task) for column in self.columns]
        print >>self.out, "|".join(cells)
# vi: ts=4 sw=4 et
