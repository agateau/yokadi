# -*- coding: UTF-8 -*-
"""
Xml rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""
from xml.dom import minidom as dom

import tui

TASK_FIELDS = ["title", "creationDate", "dueDate", "doneDate", "description", "urgency", "status", "keywords"]

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
        projectElement.setAttribute("id", unicode(project.id))

        for task in taskList:
            taskElement = self.doc.createElement("task")
            projectElement.appendChild(taskElement)

            taskElement.setAttribute("id", unicode(task.id))

            for field in TASK_FIELDS:
                if field == "keywords":
                    self._exportKeywords(taskElement, task.getKeywordDict())
                elif field == "description":
                    if task.description:
                        descriptionElement = self.doc.createElement("description")
                        taskElement.appendChild(descriptionElement)
                        descriptionElement.appendChild(self.doc.createTextNode(task.description))
                else:
                    taskElement.setAttribute(field, unicode(task.__getattribute__(field)))


    def _exportKeywords(self, taskElement, keywordDict):
        for key, value in keywordDict.items():
            keywordElement=self.doc.createElement("keyword")
            taskElement.appendChild(keywordElement)
            keywordElement.setAttribute("name", unicode(key))
            if value:
                keywordElement.setAttribute("value", unicode(value))


    def end(self):
        # FIXME: Shouldn't we use utf-8 only for xml output?
        self.out.write(self.doc.toprettyxml(indent="    ", encoding=tui.ENCODING))
# vi: ts=4 sw=4 et
