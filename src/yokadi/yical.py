# -*- coding: UTF-8 -*-
"""
Yokadi iCalendar interface

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""

import sys

try:
    import icalendar
except ImportError:
    print "You don't have the icalendar package."
    print "Get it on http://pypi.python.org/pypi/icalendar/"
    print "Or use 'easy_install icalendar'"
    sys.exit(1)

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
        length = int(self.headers.getheader('content-length'))
        cal = icalendar.Calendar.from_string(self.rfile.read(length))
        self.send_response(200)
        self.end_headers()
        for task in cal.walk():
            if not task.has_key("UID"):
                # Don't consider non task object
                continue
            if task["LAST-MODIFIED"].dt > task["CREATED"].dt:
                # Task has been modified
                print "Modified task: %s" % task["UID"]


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

