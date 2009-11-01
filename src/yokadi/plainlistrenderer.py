# -*- coding: UTF-8 -*-
"""
Simple rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import tui

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
            print >>self.out
        else:
            self.first = False
        print >>self.out, sectionName.encode(tui.ENCODING)

        for task in taskList:
            print >>self.out, (u"- " + task.title).encode(tui.ENCODING)

    def end(self):
        pass
# vi: ts=4 sw=4 et
