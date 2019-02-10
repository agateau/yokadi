# -*- coding: UTF-8 -*-
"""
Csv rendering of t_list output

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import csv

TASK_FIELDS = ["title", "creationDate", "dueDate", "doneDate", "description",
               "urgency", "status", "project", "keywords"]


class CsvListRenderer(object):
    def __init__(self, out):
        self.writer = csv.writer(out, dialect="excel")
        self._writerow(TASK_FIELDS)  # Header

    def addTaskList(self, project, taskList):
        for task in taskList:
            row = [getattr(task, field) for field in TASK_FIELDS if field != "keywords"]
            row.append(task.getKeywordsAsString())
            self._writerow(row)

    def end(self):
        pass

    def _writerow(self, row):
        self.writer.writerow([str(x) for x in row])
# vi: ts=4 sw=4 et
