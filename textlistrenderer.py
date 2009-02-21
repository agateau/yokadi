# -*- coding: UTF-8 -*-
"""
Text rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
from datetime import datetime

import colors as C
import dateutils
from db import Config


class Column(object):
    __slots__ = ["title", "width", "formater", "colorizer"]

    def __init__(self, title, width, formater, colorizer = None):
        """
        formater is a callable which accepts a task and returns a string
        colorizer is another callable which takes accepts a task and returns a
        color or None
        """
        self.title = title
        self.width = width
        self.formater = formater
        self.colorizer = colorizer


    def createHeader(self):
        return self.title.ljust(self.width)


    def createCell(self, task):
        value = self.formater(task)

        if self.colorizer:
            color = self.colorizer(task)
        else:
            color = None

        if color:
            cell = color
        else:
            cell = ""
        cell = cell + value.ljust(self.width)
        if color:
            cell = cell + C.RESET
        return cell


class TitleFormater(object):
    def __init__(self, width):
        self.width = width

    def __call__(self, task):
        title = task.title
        hasDescription = task.description != ""
        maxLength = self.width
        if hasDescription:
            maxLength -= 1
        if len(title) > maxLength:
            title = title[:maxLength - 1] + ">"
        else:
            title = title.ljust(maxLength)
        if hasDescription:
            title = title + "*"

        return title


class AgeFormater(object):
    def __init__(self):
        self.today = datetime.today().replace(microsecond=0)

    def __call__(self, task):
        return str(self.today - task.creationDate)


def urgencyColorizer(task):
    if task.urgency > 75:
        return C.RED
    elif task.urgency > 50:
        return C.PURPLE
    else:
        return None


def statusColorizer(task):
    if task.status == "started":
        return C.BOLD
    else:
        return None


def timeLeftFormater(task):
    dueDate = task.dueDate
    if dueDate:
        return dateutils.formatTimeDelta(dueDate - datetime.today().replace(microsecond=0))
    else:
        return ""


class TextListRenderer(object):
    def __init__(self, out):
        self.out = out

        titleWidth = int(Config.byName("TEXT_WIDTH").value)
        self.columns = [
            Column("ID"       , 3         , lambda x: str(x.id)),
            Column("Title"    , titleWidth, TitleFormater(titleWidth)),
            Column("U"        , 3         , lambda x: str(x.urgency)     , colorizer=urgencyColorizer),
            Column("S"        , 1         , lambda x: x.status[0].upper(), colorizer=statusColorizer),
            Column("Age"      , 18        , AgeFormater()),
            Column("Time left", 10        , timeLeftFormater),
            ]


    def addTaskList(self, project, taskList):
        self._renderTaskListHeader(project.name)
        for task in taskList:
            self._renderTaskListRow(task)


    def end(self):
        pass


    def _renderTaskListHeader(self, projectName):
        width=int(Config.byName("TEXT_WIDTH").value)

        cells = [x.createHeader() for x in self.columns]
        line = "|".join(cells)
        print >>self.out
        print >>self.out, C.CYAN+projectName.center(30+width)+C.RESET
        print >>self.out, C.BOLD+line+C.RESET
        print >>self.out, "-" * len(line)


    def _renderTaskListRow(self, task):
        cells = [column.createCell(task) for column in self.columns]
        print >>self.out, "|".join(cells)
# vi: ts=4 sw=4 et
