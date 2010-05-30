# coding:utf-8
"""
Ical features test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""


import unittest
import testutils

import tui
import yical
import dbutils

class IcalTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        tui.clearInputAnswers()

    def testUrgencyMapping(self):
        tui.addInputAnswers("y")
        t1 = dbutils.addTask("x", "t1", {})
        v1 = yical.createVTodoFromTask(t1)

        self.assertEquals(v1.get("priority"), None) # No priority

        t1.urgency = 45
        v1 = yical.createVTodoFromTask(t1)
        self.assertEquals(v1.get("priority"), 2)

        yical.updateTaskFromVTodo(t1, v1)
        self.assertEquals(t1.urgency, 45) # Ensure urgency does change

        v1.set("priority", 4)
        yical.updateTaskFromVTodo(t1, v1)
        self.assertEquals(t1.urgency, 20) # Check urgency is updated

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
            v1.set("summary", new_summary)
            yical.updateTaskFromVTodo(t1, v1)
            self.assertEqual(t1.id, origin_id)
            self.assertEqual(t1.title, "hello")

        # Update votod with fake id info.
        # Should be present in task title
        for new_summary in ("hello", "hello()", "hello(123456)", "hello (123456)"):
            v1.set("summary", new_summary)
            yical.updateTaskFromVTodo(t1, v1)
            self.assertEqual(t1.id, origin_id)
            self.assertEqual(t1.title, new_summary)
