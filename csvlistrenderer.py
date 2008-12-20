# -*- coding: UTF-8 -*-
"""
Csv rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""
import csv

import tui

TASK_FIELDS = ["title", "creationDate", "dueDate", "doneDate", "description", "urgency", "status", "project", "keywords"]

class CsvListRenderer(object):
    def __init__(self, out):
        self.writer = csv.writer(out, dialect="excel")
        self.writer.writerow(TASK_FIELDS) # Header

    def addTaskList(self, project, taskList):
        for task in taskList:
            row = list(unicode(task.__getattribute__(field)).encode(tui.ENCODING) for field in TASK_FIELDS if field!="keywords")
            row.append(task.getKeywordsAsString())
            self.writer.writerow(row)

    def end(self):
        pass
# vi: ts=4 sw=4 et
