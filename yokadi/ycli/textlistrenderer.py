# -*- coding: UTF-8 -*-
"""
Text rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""
from datetime import datetime, timedelta
from sqlalchemy.sql import func

import yokadi.ycli.colors as C
from yokadi.core import ydateutils
from yokadi.core import db
from yokadi.core.db import Task
from yokadi.ycli import tui


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

    def __init__(self, width, cryptoMgr):
        self.cryptoMgr = cryptoMgr
        self.width = width

    def __call__(self, task):
        keywords = task.getUserKeywordsNameAsString()
        hasDescription = task.description is not None and task.description != ""
        title = self.cryptoMgr.decrypt(task.title)
        # Compute title, titleWidth and colorWidth
        maxWidth = self.width
        if hasDescription:
            maxWidth -= 1
        if keywords and len(task.title) < maxWidth:
            title = self.TITLE_WITH_KEYWORDS_TEMPLATE % (title, C.BOLD + keywords)
            colorWidth = len(C.BOLD)
        else:
            colorWidth = 0

        # Adjust title to fit in self.width
        titleWidth = len(title) - colorWidth
        if titleWidth > maxWidth:
            title = title[:maxWidth - 1 + colorWidth] + C.RESET + ">"
        else:
            title = title.ljust(maxWidth + colorWidth) + C.RESET
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
    def __init__(self, today, asDate=False):
        self.today = today
        self.asDate = asDate

    def __call__(self, task):
        delta = self.today - task.creationDate.replace(microsecond=0)
        if self.asDate:
            return task.creationDate.strftime("%x %H:%M"), None
        else:
            return ydateutils.formatTimeDelta(delta), colorizer(delta.days)


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
            value = ydateutils.formatTimeDelta(delta)
        else:
            value += " (%s)" % ydateutils.formatTimeDelta(delta)

        color = colorizer(delta.days * 33, reverse=True)
        return value, color


class TextListRenderer(object):
    def __init__(self, out, termWidth=None, cryptoMgr=None, renderAsNotes=False, splitOnDate=False):
        """
        @param out: output target
        @param termWidth: terminal width (int)
        @param decrypt: whether to decrypt or not (bool)
        @param renderAsNotes: whether to display task as notes (with dates) instead of tasks (with age). (boot)"""
        self.out = out
        self.termWidth = termWidth or tui.getTermWidth()
        self.taskLists = []
        self.maxTitleWidth = len("Title")
        self.today = datetime.today().replace(microsecond=0)
        self.firstHeader = True
        self.cryptoMgr = cryptoMgr
        self.splitOnDate = splitOnDate

        if self.termWidth < 100:
            dueColumnWidth = 8
            shortDateFormat = True
        else:
            dueColumnWidth = 26
            shortDateFormat = False

        if renderAsNotes:
            self.splitOnDate = True
            creationDateColumnWidth = 16
            creationDateTitle = "Creation date"
        else:
            creationDateColumnWidth = 8
            creationDateTitle = "Age"

        # All fields set to None must be defined in end()
        self.columns = [
            Column("ID"             , None           , idFormater),
            Column("Title"          , None           , None),
            Column("U"              , 3              , urgencyFormater),
            Column("S"              , 1              , statusFormater),
            Column(creationDateTitle, creationDateColumnWidth , AgeFormater(self.today, renderAsNotes)),
            Column("Due date"       , dueColumnWidth , DueDateFormater(self.today, shortDateFormat)),
            ]

        self.idColumn = self.columns[0]
        self.titleColumn = self.columns[1]

    def addTaskList(self, sectionName, taskList):
        """Store tasks for this section
        @param sectionName: name of the task groupment section
        @type sectionName: unicode
        @param taskList: list of tasks to display
        @type taskList: list of db.Task instances
        """
        self.taskLists.append((sectionName, taskList))
        # Find max title width
        for task in taskList:
            title = self.cryptoMgr.decrypt(task.title)
            keywords = task.getUserKeywordsNameAsString()
            if keywords:
                title = TitleFormater.TITLE_WITH_KEYWORDS_TEMPLATE % (title, keywords)
            titleWidth = len(title)
            if task.description:
                titleWidth += 1
            self.maxTitleWidth = max(self.maxTitleWidth, titleWidth)

    def end(self):
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Adjust idColumn
        maxId = db.getSession().query(func.max(Task.id)).one()[0]
        self.idColumn.width = max(2, len(str(maxId)))

        # Adjust titleColumn
        self.titleColumn.width = self.maxTitleWidth
        totalWidth = sum([x.width for x in self.columns]) + len(self.columns)
        if totalWidth >= self.termWidth:
            self.titleColumn.width -= (totalWidth - self.termWidth) + len(self.columns)
        self.titleColumn.formater = TitleFormater(self.titleColumn.width, self.cryptoMgr)

        # Print table
        for sectionName, taskList in self.taskLists:
            dateSplitters = [(1, "day"), (7, "week"), (30, "month"), (30 * 4, "quarter"), (365, "year")]
            splitterRange, splitterName = dateSplitters.pop()
            splitterText = None
            self._renderTaskListHeader(sectionName)
            for task in taskList:
                while self.splitOnDate and task.creationDate > today - timedelta(splitterRange):
                    splitterText = "Last %s" % splitterName
                    if len(dateSplitters) > 0:
                        splitterRange, splitterName = dateSplitters.pop()
                    else:
                        self.splitOnDate = False

                if splitterText:
                    print(C.GREEN + splitterText.center(totalWidth) + C.RESET, file=self.out)
                    splitterText = None

                self._renderTaskListRow(task)

    def _renderTaskListHeader(self, sectionName):
        """
        @param sectionName: name used for list header
        @type sectionName: unicode"""

        cells = [x.createHeader() for x in self.columns]
        line = "|".join(cells)
        width = len(line)
        if self.firstHeader:
            self.firstHeader = False
        else:
            print(file=self.out)
        print(C.CYAN + sectionName.center(width) + C.RESET, file=self.out)
        print(C.BOLD + line + C.RESET, file=self.out)
        print("-" * width, file=self.out)

    def _renderTaskListRow(self, task):
        cells = [column.createCell(task) for column in self.columns]
        print("|".join(cells), file=self.out)
# vi: ts=4 sw=4 et
