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

from yokadi.core.db import Task, Project, DBHandler
from yokadi.core import dbutils
from yokadi.yical import icalutils
from yokadi.ycli import parseutils
from yokadi.core.yokadiexception import YokadiException

# UID pattern
UID_PREFIX = u"yokadi"
TASK_UID = UID_PREFIX + u"-task-%s"
TASK_RE = re.compile(TASK_UID.replace("%s", "(\d+)"))
PROJECT_UID = UID_PREFIX + u"-project-%s"

# Default project where new task are added
# TODO: make this a configurable items via c_set
INBOX_PROJECT = u"inbox"

# Yokadi task <=> iCalendar VTODO attribute mapping
YOKADI_ICAL_ATT_MAPPING = {u"title": u"summary",
                           u"urgency": u"priority",
                           u"creationDate": u"dtstart",
                           u"dueDate": u"due",
                           u"doneDate": u"completed",
                           u"description": u"description"}


def generateCal():
    """Generate an ical calendar from yokadi database
    @return: icalendar.Calendar object"""
    session = DBHandler.getSession()
    cal = icalendar.Calendar()
    cal.add("prodid", '-//Yokadi calendar //yokadi.github.com//')
    cal.add("version", "2.0")
    # Add projects
    for project in session.query(Project).filter(Project.active == True):
        vTodo = icalendar.Todo()
        vTodo.add("summary", project.name)
        vTodo["uid"] = PROJECT_UID % project.id
        cal.add_component(vTodo)
    # Add tasks
    for task in session.query(Task).filter(Task.status != "done"):
        vTodo = createVTodoFromTask(task)
        cal.add_component(vTodo)

    return cal


def createVTodoFromTask(task):
    """Create a VTodo object from a yokadi task
    @param task: yokadi task (db.Task object)
    @return: ical VTODO (icalendar.Calendar.Todo object)"""
    vTodo = icalendar.Todo()
    vTodo["uid"] = TASK_UID % task.id
    vTodo["related-to"] = PROJECT_UID % task.project.id

    # Add standard attribute
    for yokadiAttribute, icalAttribute in YOKADI_ICAL_ATT_MAPPING.items():
        attr = getattr(task, yokadiAttribute)
        if attr:
            if yokadiAttribute == "urgency":
                attr = icalutils.yokadiUrgencyToIcalPriority(attr)
            if yokadiAttribute == "title":
                attr += " (%s)" % task.id
            vTodo.add(icalAttribute, attr)

    # Add categories from keywords
    categories = []
    if task.taskKeywords:
        for name, value in task.getKeywordDict().items():
            if value:
                categories.append("%s=%s" % (name, value))
            else:
                categories.append(name)
    vTodo.add("categories", categories)

    return vTodo


def updateTaskFromVTodo(task, vTodo):
    """Update a yokadi task with an ical VTODO object
    @param task: yokadi task (db.Task object)
    @param vTodo: ical VTODO (icalendar.Calendar.Todo object)"""
    for yokadiAttribute, icalAttribute in YOKADI_ICAL_ATT_MAPPING.items():
        attr = vTodo.get(icalAttribute)
        if attr:
            # Convert ical type (vDates, vInt..) to sql alchemy understandable type (datetime, int...)
            attr = icalutils.convertIcalType(attr)
            if yokadiAttribute == "title":
                # Remove (id)
                attr = re.sub("\s?\(%s\)" % task.id, "", attr)
            if yokadiAttribute == "doneDate":
                # A done date defined indicate that task is done
                task.status = "done"
                # BUG: Done date is UTC, we must compute local time for yokadi
            if yokadiAttribute == "urgency":
                if attr == icalutils.yokadiUrgencyToIcalPriority(task.urgency):
                    # Priority does not change - don't update it
                    continue
                else:
                    # Priority has changed, we need to update urgency
                    attr = icalutils.icalPriorityToYokadiUrgency(int(attr))

            # Update attribute
            setattr(task, yokadiAttribute, attr)

    # Update keywords from categories
    if vTodo.get("categories"):
        if isinstance(vTodo.get("categories"), (list)):
            categories = vTodo.get("categories")
        else:
            categories = vTodo.get("categories").split(",")

        keywords = ["@%s" % k for k in categories]
        garbage, keywordFilters = parseutils.extractKeywords(" ".join(keywords))
        newKwDict = parseutils.keywordFiltersToDict(keywordFilters)
        if garbage:
            print "Got garbage while parsing categories: %s" % garbage
        dbutils.createMissingKeywords(newKwDict.keys(), interactive=False)
        task.setKeywordDict(newKwDict)

class IcalHttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Simple Ical http request handler that only implement GET method"""
    newTask = {}  # Dict recording new task origin UID

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
        for vTodo in cal.walk():
            if "UID" in vTodo:
                try:
                    self._processVTodo(vTodo)
                except YokadiException, e:
                    self.send_response(503, e)

        # Tell caller everything is ok
        self.send_response(200)
        self.end_headers()

    def _processVTodo(self, vTodo):
        session = DBHandler.getSession()
        if vTodo["UID"] in self.newTask:
            # This is a recent new task but remote ical calendar tool is not
            # aware of new Yokadi UID. Update it here to avoid duplicate new tasks
            print "update UID to avoid duplicate task"
            vTodo["UID"] = TASK_UID % self.newTask[vTodo["UID"]]

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
                    session.merge(task)
                    session.commit()
                else:
                    raise YokadiException("Task %s does exist in yokadi db " % id)
        else:
            # This is a new task
            print "New task %s (%s)" % (vTodo["summary"], vTodo["UID"])
            keywordDict = {}
            task = dbutils.addTask(INBOX_PROJECT, vTodo["summary"],
                               keywordDict, interactive=False)
            session.add(task)
            session.commit()
            # Keep record of new task origin UID to avoid duplicate
            # if user update it right after creation without reloading the
            # yokadi UID
            # TODO: add purge for old UID
            self.newTask[vTodo["UID"]] = task.id


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

# vi: ts=4 sw=4 et
