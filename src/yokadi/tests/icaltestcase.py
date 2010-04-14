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

