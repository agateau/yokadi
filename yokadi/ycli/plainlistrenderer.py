# -*- coding: UTF-8 -*-
"""
Simple rendering of t_list output

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""


class PlainListRenderer(object):
    def __init__(self, out):
        self.out = out
        self.first = True

    def addTaskList(self, sectionName, taskList):
        """Store tasks for this section
        @param sectionName: name of the task groupement section
        @type sectionName: unicode
        @param taskList: list of tasks to display
        @type taskList: list of db.Task instances
        """

        if not self.first:
            print(file=self.out)
        else:
            self.first = False
        print(sectionName, file=self.out)

        for task in taskList:
            print(("- " + task.title), file=self.out)

    def end(self):
        pass
# vi: ts=4 sw=4 et
