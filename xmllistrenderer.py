# -*- coding: UTF-8 -*-
"""
Xml rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
import sys
from xml.dom import minidom as dom

import tui

TASK_FIELDS = ["title", "creationDate", "dueDate", "doneDate", "description", "urgency", "status", "project", "keywords"]

class XmlListRenderer(object):
    def __init__(self, out):
        self.out = out
        self.doc = dom.Document()
        self.rootElement = self.doc.createElement("yokadi")
        self.doc.appendChild(self.rootElement)


    def addTaskList(self, project, taskList):
        projectElement = self.doc.createElement("project")
        self.rootElement.appendChild(projectElement)
        projectElement.setAttribute("name", project.name)

        tasksElement = self.doc.createElement("tasks")
        projectElement.appendChild(tasksElement)

        for task in taskList:
            taskElement = self.doc.createElement("task")
            tasksElement.appendChild(taskElement)

            for field in TASK_FIELDS:
                if field=="keywords": continue
                taskElement.setAttribute(field, unicode(task.__getattribute__(field)))

            for key, value in task.getKeywordDict().items():
                keywordElement=self.doc.createElement("keyword")
                taskElement.appendChild(keywordElement)
                keywordElement.setAttribute(key, unicode(value))

            tasksElement.appendChild(taskElement)


    def end(self):
        # FIXME: Shouldn't we use utf-8 only for xml output?
        self.out.write(self.doc.toprettyxml(indent="    ", encoding=tui.ENCODING))
# vi: ts=4 sw=4 et
