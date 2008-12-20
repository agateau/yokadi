# -*- coding: UTF-8 -*-
"""
Helper functions to render formated text on screen

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import colors as C

class TextRenderer(object):
    def renderTaskSummary(self, task):
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
            fields.append(("Done", task.doneDate))

        self.renderFields(fields)


    def renderFields(self, fields):
        """Print on screen tabular array represented by fields
        @param fields: list of tuple (caption, value)
        """
        maxWidth = max([len(x) for x,y in fields])
        format=C.BOLD+"%" + str(maxWidth) + "s"+C.RESET+": %s"
        for caption, value in fields:
            print format % (caption, value)

# vi: ts=4 sw=4 et
