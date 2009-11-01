# -*- coding: UTF-8 -*-
"""
Xml rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
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


    def addTaskList(self, sectionName, taskList):
        """Store tasks for this section
        @param sectionName: name of the task groupement section
        @type sectionName: unicode
        @param taskList: list of tasks to display
        @type taskList: list of db.Task instances
        """

        sectionElement = self.doc.createElement("section")
        self.rootElement.appendChild(sectionElement)
        sectionElement.setAttribute("name", sectionName)


        for task in taskList:
            taskElement = self.doc.createElement("task")
            sectionElement.appendChild(taskElement)

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
