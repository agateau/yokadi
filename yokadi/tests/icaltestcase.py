# coding:utf-8
"""
Ical features test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""


import unittest
from datetime import datetime, timedelta

import icalendar

from yokadi.ycli import tui
from yokadi.ycli.projectcmd import getProjectFromName
from yokadi.yical import yical
from yokadi.core import dbutils
from yokadi.core import db


class IcalTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()
        tui.clearInputAnswers()

    def testUrgencyMapping(self):
        tui.addInputAnswers("y")
        t1 = dbutils.addTask("x", "t1", {})
        v1 = yical.createVTodoFromTask(t1)

        self.assertEqual(v1.get("priority"), None)  # No priority

        t1.urgency = 45
        v1 = yical.createVTodoFromTask(t1)
        self.assertEqual(v1.get("priority"), 2)

        yical.updateTaskFromVTodo(t1, v1)
        self.assertEqual(t1.urgency, 45)  # Ensure urgency does change

        v1["priority"] = 4
        yical.updateTaskFromVTodo(t1, v1)
        self.assertEqual(t1.urgency, 20)  # Check urgency is updated

    def testTitleMapping(self):
        tui.addInputAnswers("y")
        t1 = dbutils.addTask("x", "t1", {})
        v1 = yical.createVTodoFromTask(t1)

        # Check id is here
        self.assertEqual(v1.get("summary")[-4:], " (%s)" % t1.id)

        # Title and id should not change with update
        origin_id = t1.id
        origin_title = t1.title
        yical.updateTaskFromVTodo(t1, v1)
        self.assertEqual(t1.id, origin_id)
        self.assertEqual(t1.title, origin_title)

        # Update vtodo summary and remove (id) or space before (id) info.
        # Only task title should be changed
        for new_summary in ("hello", "hello(%s)" % origin_id, "hello (%s)" % origin_id,
                            "(%s)hello" % origin_id, " (%s)hello" % origin_id):
            v1["summary"] = new_summary
            yical.updateTaskFromVTodo(t1, v1)
            self.assertEqual(t1.id, origin_id)
            self.assertEqual(t1.title, "hello")

        # Update votod with fake id info.
        # Should be present in task title
        for new_summary in ("hello", "hello()", "hello(123456)", "hello (123456)"):
            v1["summary"] = new_summary
            yical.updateTaskFromVTodo(t1, v1)
            self.assertEqual(t1.id, origin_id)
            self.assertEqual(t1.title, new_summary)

    def testKeywordMapping(self):
        tui.addInputAnswers("y")
        tui.addInputAnswers("y")
        tui.addInputAnswers("y")
        t1 = dbutils.addTask("x", "t1", {"k1": None, "k2": 123})
        v1 = yical.createVTodoFromTask(t1)

        # Check categories are created
        categories = [str(c) for c in v1.get("categories")]
        categories.sort()
        self.assertEqual(categories, ["k1", "k2=123"])

        # Check keywords are still here
        yical.updateTaskFromVTodo(t1, v1)
        keywords = list(t1.getKeywordDict().keys())
        self.session.commit()
        keywords.sort()
        self.assertEqual(keywords, ["k1", "k2"])
        self.assertEqual(t1.getKeywordDict()["k2"], 123)

        # Remove k2 category
        v1["categories"] = ["k1"]
        yical.updateTaskFromVTodo(t1, v1)
        self.session.commit()
        self.assertEqual(list(t1.getKeywordDict().keys()), ["k1", ])

        # Set k1 value
        v1["categories"] = ["k1=456", ]
        yical.updateTaskFromVTodo(t1, v1)
        self.session.commit()
        self.assertEqual(t1.getKeywordDict()["k1"], 456)

        # Create a category
        v1["categories"] = ["k1", "k4=789"]
        yical.updateTaskFromVTodo(t1, v1)
        keywords = list(t1.getKeywordDict().keys())
        keywords.sort()
        self.assertEqual(keywords, ["k1", "k4"])
        self.assertEqual(t1.getKeywordDict()["k4"], 789)

    def testTaskDoneMapping(self):
        tui.addInputAnswers("y")
        t1 = dbutils.addTask("x", "t1", {})
        v1 = yical.createVTodoFromTask(t1)

        completed = datetime.now()
        v1.add("COMPLETED", completed)
        yical.updateTaskFromVTodo(t1, v1)
        self.assertEqual(t1.status, "done")
        self.assertEqual(t1.doneDate, completed)

    def testGenerateCal(self):
        # Add an inactive project
        t1 = dbutils.addTask("p1", "t1", interactive=False)
        project = getProjectFromName("p1")
        project.active = False

        # And an active project with 3 tasks, one of them is done
        t2new = dbutils.addTask("p2", "t2new", interactive=False)

        t2started = dbutils.addTask("p2", "t2started", interactive=False)
        t2started.setStatus("started")

        t2done = dbutils.addTask("p2", "t2done", interactive=False)
        t2done.setStatus("done")

        self.session.commit()

        # Generate the calendar
        cal = yical.generateCal()

        # It should contain only "p2", "t1" and "t2new" and "t2started"
        # I am not sure that it should contain "t1" (since its project is not active), but that's the current behavior
        summaries = sorted(str(x["SUMMARY"]) for x in cal.subcomponents)
        expected = sorted(["p2", f"t1 ({t1.id})", f"t2new ({t2new.id})", f"t2started ({t2started.id})"])

        self.assertEqual(summaries, expected)

    def testHandlerProcessVTodoModifyTask(self):
        # Create a task
        task = dbutils.addTask("p1", "t1", interactive=False)
        self.session.commit()

        # Create a vTodo to modify the task
        modified = datetime.now()
        created = modified + timedelta(hours=-1)
        vTodo = icalendar.Todo()
        vTodo["UID"] = yical.TASK_UID % str(task.id)
        vTodo.add("CREATED", created)
        vTodo.add("LAST-MODIFIED", modified)
        vTodo.add("summary", "new title")

        # Process the vTodo
        newTaskDict = {}
        yical.IcalHttpRequestHandler.processVTodo(newTaskDict, vTodo)

        # The task title must have changed
        task = dbutils.getTaskFromId(task.id)
        self.assertEqual(task.title, "new title")

        # newTaskDict must not have changed
        self.assertEqual(newTaskDict, {})

    def testHandlerProcessVTodoCreateTask(self):
        # Create a vTodo to add a new task
        vTodo = icalendar.Todo()
        vTodo["UID"] = "zogzog"
        vTodo.add("summary", "new task")

        # Process the vTodo
        newTaskDict = {}
        yical.IcalHttpRequestHandler.processVTodo(newTaskDict, vTodo)

        # The task should be in newTaskDict
        newTaskList = list(newTaskDict.items())
        self.assertEqual(len(newTaskList), 1)

        (uid, taskId) = newTaskList[0]

        # And the task can be retrieved
        task = dbutils.getTaskFromId(taskId)
        self.assertEqual(task.title, "new task")

        # And there is only one task
        self.assertEqual(self.session.query(db.Task).count(), 1)
