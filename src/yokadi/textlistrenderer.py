# -*- coding: UTF-8 -*-
"""
Text rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
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
            cell = color + value.ljust(self.width) + C.RESET
        else:
            cell = value.ljust(self.width)

        return cell


def idFormater(task):
    return str(task.id), None

class TitleFormater(object):
    TITLE_WITH_KEYWORDS_TEMPLATE = "%s (%s)"
    def __init__(self, width):
        self.width = width

    def __call__(self, task):
        # Compute title, titleWidth and colorWidth
        keywords = task.getUserKeywordsNameAsString()
        if keywords:
            title = self.TITLE_WITH_KEYWORDS_TEMPLATE % (task.title, C.BOLD + keywords + C.RESET)
            colorWidth = len(C.BOLD) + len(C.RESET)
        else:
            title = task.title
            colorWidth = 0
        titleWidth = len(title) - colorWidth

        # Adjust title to fit in self.width
        maxWidth = self.width
        hasDescription = task.description != ""
        if hasDescription:
            maxWidth -= 1
        if titleWidth > maxWidth:
            title = title[:maxWidth - 1] + ">"
        else:
            title = title.ljust(maxWidth + colorWidth)
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
    def __init__(self, out, termWidth = None):
        self.out = out
        self.termWidth = termWidth or tui.getTermWidth()
        self.taskLists = []
        self.maxTitleWidth = len("Title")
        self.today = datetime.today().replace(microsecond=0)

        # All fields set to None must be defined in end()
        self.columns = [
            Column("ID"       , None        , idFormater),
            Column("Title"    , None        , None),
            Column("U"        , 3           , urgencyFormater),
            Column("S"        , 1           , statusFormater),
            Column("Age"      , 8           , AgeFormater(self.today)),
            Column("Due date" , None        , None),
            ]

        self.idColumn = self.columns[0]
        self.titleColumn = self.columns[1]
        self.dueColumn = self.columns[-1]


    def addTaskList(self, sectionName, taskList):
        """Store tasks for this section
        @param sectionName: name of the task groupement section
        @type sectionName: unicode
        @param taskList: list of tasks to display
        @type taskList: list of db.Task instances
        """
        self.taskLists.append((sectionName, taskList))
        # Find max title width
        for task in taskList:
            title = task.title
            keywords = task.getUserKeywordsNameAsString()
            if keywords:
                title = TitleFormater.TITLE_WITH_KEYWORDS_TEMPLATE % (title, keywords)
            titleWidth = len(title)
            if task.description:
                titleWidth += 1
            self.maxTitleWidth = max(self.maxTitleWidth, titleWidth)

    def end(self):
        # Adjust idColumn
        maxId = Task.select().max(Task.q.id)
        self.idColumn.width = max(2, len(str(maxId)))

        # Adjust dueColumn
        shortDateFormat = self.termWidth < 100
        if shortDateFormat:
            self.dueColumn.width = 8
        else:
            self.dueColumn.width = 26
        self.dueColumn.formater = DueDateFormater(self.today, shortDateFormat)

        # Adjust titleColumn
        self.titleColumn.width = self.maxTitleWidth
        totalWidth = sum([x.width for x in self.columns])
        if totalWidth > self.termWidth:
            self.titleColumn.width -= (totalWidth - self.termWidth) + len(self.columns)
        self.titleColumn.formater = TitleFormater(self.titleColumn.width)

        # Print table
        for sectionName, taskList in self.taskLists:
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
