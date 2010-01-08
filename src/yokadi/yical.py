# -*- coding: UTF-8 -*-
"""
Yokadi iCalendar interface

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""

import icalendar
import BaseHTTPServer
from threading import Thread


from db import Task, Project

# UID pattern
TASK_UID = "yokadi-task-%s"
PROJECT_UID = "yokadi-project-%s"

def generateCal():
    cal = icalendar.Calendar()
    cal.add("prodid", '-//Yokadi calendar //yokadi.github.com//')
    cal.add("version", "2.0")
    # Add projects
    for project in Project.select(Project.q.active == True):
        todo = icalendar.Todo()
        todo.add("summary", project.name)
        todo["uid"] = PROJECT_UID % project.id
        cal.add_component(todo)
    # Add tasks
    for task in Task.select(Task.q.status != "done"):
        todo = icalendar.Todo()
        todo["uid"] = TASK_UID % task.id
        todo["related-to"] = PROJECT_UID % task.project.id
        todo.add("dtstamp", task.creationDate)
        todo.add("priority", task.urgency)
        todo.add("summary", "%s (%s)" % (task.title, task.id))
        todo.add("dtstart", task.creationDate)
        if task.dueDate:
            todo.add("due", task.dueDate)
        if task.description:
            todo.add("description", task.description)
        categories = [task.project, ] # Add project as a keyword
        if task.keywords:
            categories.extend([k.name for k in task.keywords])
        todo.add("categories", categories)
        cal.add_component(todo)

    return cal

class IcalHttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Simple Ical http request handler that only implement GET method"""
    def do_GET(self):
        """Serve a GET request with complete todolist ignoring path"""
        self.send_response(200)
        self.end_headers()
        cal = generateCal()
        self.wfile.write(cal.as_string())

    def do_PUT(self):
        """Receive a todolist for updating"""
        pass

class YokadiIcalServer(Thread):
    def __init__(self, port, listen):
        self.port = port
        if listen:
            self.address = ""
        else:
            self.address = "127.0.0.1"
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        """Method executed when the thread object start() method is called"""
        print "IcalServer starting..."
        icalServer = BaseHTTPServer.HTTPServer((self.address, self.port), IcalHttpRequestHandler)
        icalServer.serve_forever()
        print "IcalServer crash. Oups !"

