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


class TextListRenderer(object):
    def __init__(self, out):
        self.out = out


    def addTaskList(self, project, taskList):
        self._renderTaskListHeader(project.name)
        for task in taskList:
            self._renderTaskListRow(task)


    def end(self):
        pass


    def _getTaskFormat(self):
        """@return: task format as a string with placeholder"""
        width=Config.byName("TEXT_WIDTH").value
        return "%(id)-3s|%(title)-"+width+"s|%(urgency)-3s|%(status)-1s|%(creationDate)-16s|%(timeLeft)-10s"


    def _renderTaskListHeader(self, projectName):
        width=int(Config.byName("TEXT_WIDTH").value)
        line = self._getTaskFormat() % dict(id="ID", title="Title", urgency="U",
                                       status="S", creationDate="Creation date", timeLeft="Time left")
        print >>self.out
        print >>self.out, C.CYAN+projectName.center(30+width)+C.RESET
        print >>self.out, C.BOLD+line+C.RESET
        print >>self.out, "-" * len(line)


    def _renderTaskListRow(self, task):
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
            timeLeft=dateutils.formatTimeDelta(task.dueDate - datetime.today().replace(microsecond=0))
        else:
            timeLeft=""
        if int(task.urgency)>75:
            urgency=C.RED+str(task.urgency)+" "+C.RESET
        elif int(task.urgency)>50:
            urgency=C.PURPLE+str(task.urgency)+" "+C.RESET
        else:
            urgency=task.urgency

        print >>self.out, self._getTaskFormat() % dict(id=str(task.id), title=title, urgency=urgency, status=status,
                                       creationDate=creationDate, timeLeft=timeLeft)
# vi: ts=4 sw=4 et
