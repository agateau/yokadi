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
import re

from db import Task, Project
import dbutils
from dbutils import updateTask

# UID pattern
UID_PREFIX = "yokadi"
TASK_UID = UID_PREFIX + "-task-%s"
TASK_RE = re.compile(TASK_UID.replace("%s", "(\d+)"))
PROJECT_UID = UID_PREFIX + "-project-%s"

# Default project where new task are added
# TODO: make this a configurable items via c_set
INBOX_PROJECT = "inbox"

# Yokadi task <=> iCalendar VTODO attribute mapping
YOKADI_ICAL_ATT_MAPPING = {"title" : "summary",
                           "urgency" : "priority",
                           "creationDate": "dtstart",
                           "dueDate" : "due",
                           "description" : "description" }

def generateCal():
    """Generate an ical calendar from yokadi database"""
    cal = icalendar.Calendar()
    cal.add("prodid", '-//Yokadi calendar //yokadi.github.com//')
    cal.add("version", "2.0")
    # Add projects
    for project in Project.select(Project.q.active == True):
        vTodo = icalendar.Todo()
        vTodo.add("summary", project.name)
        vTodo["uid"] = PROJECT_UID % project.id
        cal.add_component(vTodo)
    # Add tasks
    for task in Task.select(Task.q.status != "done"):
        #TODO: use dict mapping for standard attributes
        vTodo = icalendar.Todo()
        vTodo["uid"] = TASK_UID % task.id
        vTodo["related-to"] = PROJECT_UID % task.project.id
        vTodo.add("priority", task.urgency)
        vTodo.add("summary", "%s (%s)" % (task.title, task.id))
        vTodo.add("dtstart", task.creationDate)
        if task.dueDate:
            vTodo.add("due", task.dueDate)
        if task.description:
            vTodo.add("description", task.description)
        categories = [task.project, ] # Add project as a keyword
        if task.keywords:
            categories.extend([k.name for k in task.keywords])
        vTodo.add("categories", categories)
        cal.add_component(vTodo)

    return cal

def updateTaskFromVTodo(task, vTodo):
    """Update a yokadi task with an ical VTODO object
    @param task: yokadi task (db.Task object)
    @param vTodo: ical VTODO (icalendar.Calendar.Todo object)"""

    for yokadiAttribute, icalAttribute in YOKADI_ICAL_ATT_MAPPING.items():
        attr = vTodo.get(icalAttribute)
        print "%s : %s" % (icalAttribute, attr)
        if attr:
            if yokadiAttribute == "title":
                # Remove (id)
                attr = re.sub(" \(\d+\)$", "", attr)
            if isinstance(attr, (icalendar.vDate, icalendar.vDatetime,
                                 icalendar.vDuration, icalendar.vDDDTypes)):
                attr = attr.dt
            # Update attribute
            setattr(task, yokadiAttribute, attr)


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
        for vTodo in cal.walk():
            if not vTodo.has_key("UID"):
                # Don't consider non task object
                continue
            if vTodo["UID"].startswith(UID_PREFIX):
                # This is a yokadi Task.
                if vTodo["LAST-MODIFIED"].dt > vTodo["CREATED"].dt:
                    # Task has been modified
                    print "Modified task: %s" % vTodo["UID"]
                    result = TASK_RE.match(vTodo["UID"])
                    if result:
                        id = result.group(1)
                        task = dbutils.getTaskFromId(id)
                        print "Task found in yokadi db: %s" % task.title
                        updateTaskFromVTodo(task, vTodo)
                    else:
                        print "Task %s does exist in yokadi db " % id
            else:
                # This is a new task
                print "New task %s (%s)" % (vTodo["summary"], vTodo["UID"])
                keywordDict = {}
                task = dbutils.addTask(INBOX_PROJECT, vTodo["summary"],
                                       keywordDict, interactive=False)

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

