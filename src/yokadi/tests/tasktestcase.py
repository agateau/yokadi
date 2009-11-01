# -*- coding: UTF-8 -*-
"""
Task test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest

import testutils

import tui
from db import Project, Task
from taskcmd import TaskCmd
from yokadiexception import YokadiException

class TaskTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        tui.clearInputAnswers()
        self.cmd = TaskCmd()

    def testAdd(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")

        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x @kw1 @kw2=12 t2")

        tasks = list(Task.select())
        result = [x.title for x in tasks]
        expected = [u"t1", u"t2"]
        self.assertEqual(result, expected)

        kwDict = Task.get(2).getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))

    def testMark(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task = Task.get(1)
        self.assertEqual(task.status, "new")
        self.cmd.do_t_mark_started("1")
        self.assertEqual(task.status, "started")
        self.cmd.do_t_mark_done("1")
        self.assertEqual(task.status, "done")

    def testAddKeywords(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task = Task.get(1)

        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add_keywords("1 @kw1 @kw2=12")

        kwDict = task.getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))

    def testLastTaskId(self):
        # Using "_" with no prior task activity should raise an exception   
        self.assertRaises(YokadiException, self.cmd.getTaskFromId, "_")

        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task1 = Task.get(1)
        self.assertEqual(self.cmd.getTaskFromId("_"), task1)

        self.cmd.do_t_add("x t2")
        task2 = Task.get(2)
        self.assertEqual(self.cmd.getTaskFromId("_"), task2)

        self.cmd.do_t_mark_started("1")
        self.assertEqual(self.cmd.getTaskFromId("_"), task1)

    def testRecurs(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task = Task.get(1)
        self.cmd.do_t_recurs("1 daily 10:00")
        desc = str(task.recurrence)
        self.cmd.do_t_recurs("1 weekly FR 23:00")
        self.cmd.do_t_recurs("1 weekly fr 23:00")
        self.cmd.do_t_recurs("1 weekly Fr 23:00")
        self.cmd.do_t_recurs("1 weekly Friday 23:00")
        self.cmd.do_t_recurs("1 monthly 3 13:00")
        self.cmd.do_t_recurs("1 monthly second friday 13:00")
        self.cmd.do_t_recurs("1 yearly 3/07 11:20")
        self.cmd.do_t_recurs("1 quarterly 14 11:20")
        self.cmd.do_t_recurs("1 quarterly first monday 23:20")
        self.assertNotEqual(desc, str(task.recurrence))
        self.assertEqual(task.status, "new")
        self.cmd.do_t_mark_done("1")
        self.assertEqual(task.status, "new")

    def testTlist(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x @kw1 @kw2=12 t2")

        for line in ("", "-a", "-t", "-d today", "-u", "-k %", "-k _%", "-s t", "--overdue",
                     "-f plain", "-f xml", "-f html"):
            self.cmd.do_t_list(line)
# vi: ts=4 sw=4 et
