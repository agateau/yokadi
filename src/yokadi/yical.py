# -*- coding: UTF-8 -*-
"""
Yokadi iCalendar interface

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""

import sys
import icalendar
import BaseHTTPServer
from threading import Thread
from sqlobject import AND

import tui
# Force default encoding to prefered encoding
reload(sys)
sys.setdefaultencoding(tui.ENCODING)


from db import Task, Project

def generateCal():
    cal = icalendar.Calendar()
    cal.add("prodid", '-//Yokadi calendar //yokadi.github.com//')
    cal.add("version", "1.0")
    # Add projects
    for project in Project.select(Project.q.active == True):
        todo = icalendar.Todo()
        todo.add("summary", project.name)
        todo["uid"] = "p%s" % project.id
        cal.add_component(todo)
    # Add tasks
    for task in Task.select(Task.q.status != "done"):
        todo = icalendar.Todo()
        todo["uid"] = "t%s" % task.id
        todo["related-to"] = "p%s" % task.project.id
        todo.add("dtstamp", task.creationDate)
        todo.add("priority", task.urgency)
        todo.add("summary", task.title)
        todo.add("dtstart", task.creationDate)
        if task.dueDate:
            todo.add("due", task.dueDate)
        if task.description:
            todo.add("description", task.description)
        if task.keywords:
            todo.add("categories", [k.name for k in task.keywords])
        cal.add_component(todo)

    return cal

class IcalHttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Simple Ical http request handler that only implement GET method"""
    def do_GET(self):
        """Serve a GET request with complete todolist ignoring path"""
        self.send_response(200)
        self.send_header("Content-Type", "text/calendar;charset=UTF-8")
        self.end_headers()
        cal = generateCal()
        self.wfile.write(cal.as_string())

    def do_PUT(self):
        """Receive a todolist for updating"""
        pass

class YokadiIcalServer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        """Method executed when the thread object start() method is called"""
        print "Yokadi IcalServer starting..."
        icalServer = BaseHTTPServer.HTTPServer(("", 8000), IcalHttpRequestHandler)
        icalServer.serve_forever()
        print "Yokadi IcalServer exiting..."

