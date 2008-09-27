# -*- coding: UTF-8 -*-
"""
Helper functions to render formated text on screen

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import colors as C
from datetime import datetime
from utils import formatTimeDelta
from db import Config
from sqlobject import SQLObjectNotFound

class TextRenderer(object):

    def getTaskFormat(self):
        """@return: task format as a string with placeholder"""
        width=Config.byName("TEXT_WIDTH").value
        return "%(id)-3s|%(title)-"+width+"s|%(urgency)-3s|%(status)-1s|%(creationDate)-16s|%(timeLeft)-10s"

    def renderTaskListHeader(self, projectName):
        width=int(Config.byName("TEXT_WIDTH").value)
        line = self.getTaskFormat() % dict(id="ID", title="Title", urgency="U",
                                       status="S", creationDate="Creation date", timeLeft="Time left")
        print
        print C.CYAN+projectName.center(30+width)+C.RESET
        print C.BOLD+line+C.RESET
        print "-" * len(line)


    def renderTaskListRow(self, task):
        title = task.title
        hasDescription = task.description != ""
        maxLength = int(Config.byName("TEXT_WIDTH").value)
        if hasDescription:
            maxLength -=1
        if len(title) > maxLength:
            title = title[:maxLength - 1] + ">"
        if hasDescription:
            title = title.ljust(maxLength) + "*"

        status = task.status[0].upper()
        if status=="S":
            status=C.BOLD+status+C.RESET
        creationDate = str(task.creationDate)[:-3]
        if task.dueDate:
            timeLeft=formatTimeDelta(task.dueDate - datetime.today().replace(microsecond=0))
        else:
            timeLeft=""
        if int(task.urgency)>75:
            urgency=C.RED+str(task.urgency)+" "+C.RESET
        elif int(task.urgency)>50:
            urgency=C.PURPLE+str(task.urgency)+" "+C.RESET
        else:
            urgency=task.urgency

        print self.getTaskFormat() % dict(id=str(task.id), title=title, urgency=urgency, status=status,
                                       creationDate=creationDate, timeLeft=timeLeft)


    def renderTaskDetails(self, task):
        keywordDict = task.getKeywordDict()
        keywordArray = []
        for name, value in keywordDict.items():
            txt = name
            if value:
                txt += "=" + str(value)
            keywordArray.append(txt)
            keywordArray.sort()
        keywords = ", ".join(keywordArray)
        fields = [
            ("Project", task.project.name),
            ("Title", task.title),
            ("Created", task.creationDate),
            ("Due", task.dueDate),
            ("Status", task.status),
            ("Urgency", task.urgency),
            ("Keywords", keywords),
            ]

        if task.status == "done":
            fields.append(
                (C.BOLD+"Done"+C.RESET, task.doneDate),
                )

        self.renderFields(fields)

        if task.description != '':
            print
            print task.description

    def renderFields(self, fields):
        """Print on screen tabular array represented by fields
        @param fields: list of tuple (caption, value)
        """
        maxWidth = max([len(x) for x,y in fields])
        format=C.BOLD+"%" + str(maxWidth) + "s"+C.RESET+": %s"
        for caption, value in fields:
            print format % (caption, value)

# vi: ts=4 sw=4 et
