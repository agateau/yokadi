# -*- coding: UTF-8 -*-
"""
Simple rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import tui

class PlainListRenderer(object):
    def __init__(self, out):
        self.out = out
        self.first = True

    def addTaskList(self, project, taskList):
        if not self.first:
            print >>self.out
        else:
            self.first = False
        print >>self.out, project.name.encode(tui.ENCODING)

        for task in taskList:
            print >>self.out, (u"- " + task.title).encode(tui.ENCODING)

    def end(self):
        pass
# vi: ts=4 sw=4 et
