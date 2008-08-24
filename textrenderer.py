# -*- coding: UTF-8 -*-
"""
Helper functions to render formated text on screen

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import colors as C

TASK_LIST_FORMAT="%(id)-3s|%(title)-60s|%(urgency)-3s|%(status)-1s|%(creationDate)-19s"

class TextRenderer(object):
    def renderTaskListHeader(self, projectName):
        line = TASK_LIST_FORMAT % dict(id="ID", title="Title", urgency="U", status="S", creationDate="Date")
        print
        print C.CYAN+projectName.center(90)+C.RESET
        print C.BOLD+line+C.RESET
        print "-" * len(line)


    def renderTaskListRow(self, task):
        title = task.title
        hasDescription = task.description != ""
        maxLength = 60
        if hasDescription:
            maxLength -=1
        if len(title) > maxLength:
            title = title[:maxLength - 1] + ">"
        if hasDescription:
            title = title.ljust(maxLength) + "*"

        status = task.status[0].upper()
        if status=="S":
            status=C.BOLD+status+C.RESET
        creationDate = task.creationDate

        if int(task.urgency)>75:
            urgency=C.RED+str(task.urgency)+" "+C.RESET
        elif int(task.urgency)>50:
            urgency=C.PURPLE+str(task.urgency)+" "+C.RESET
        else:
            urgency=task.urgency

        print TASK_LIST_FORMAT % dict(id=str(task.id), title=title, urgency=urgency, status=status, creationDate=creationDate)


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
            (C.BOLD+"Project"+C.RESET, task.project.name),
            (C.BOLD+"Title"+C.RESET, task.title),
            (C.BOLD+"Created"+C.RESET, task.creationDate),
            (C.BOLD+"Status"+C.RESET, task.status),
            (C.BOLD+"Urgency"+C.RESET, task.urgency),
            (C.BOLD+"Keywords"+C.RESET, keywords),
            ]

        if task.status == "done":
            fields.append(
                ("Done", task.doneDate),
                )

        maxWidth = max([len(x) for x,y in fields])
        format="%" + str(maxWidth) + "s: %s"
        for caption, value in fields:
            print format % (caption, value)

        if task.description != '':
            print
            print task.description
# vi: ts=4 sw=4 et
