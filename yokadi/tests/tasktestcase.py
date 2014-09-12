# -*- coding: UTF-8 -*-
"""
Task test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import sys
import unittest
from io import StringIO

import testutils

from yokadi.ycli import tui
from yokadi.ycli.main import YokadiCmd
from yokadi.core import cryptutils
from yokadi.core import db
from yokadi.core import dbutils
from yokadi.core.db import Task, TaskLock, Keyword, Recurrence, setDefaultConfig
from yokadi.core.yokadiexception import YokadiException, BadUsageException


class TaskTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        setDefaultConfig()
        self.session = db.getSession()
        tui.clearInputAnswers()
        self.cmd = YokadiCmd()

    def testAdd(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")

        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x @kw1 @kw2=12 t2")

        tui.addInputAnswers("n")
        self.cmd.do_t_add("notExistingProject newTask")

        tasks = self.session.query(Task).all()
        result = [x.title for x in tasks]
        expected = ["t1", "t2"]
        self.assertEqual(result, expected)

        kwDict = self.session.query(Task).get(2).getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))

        for bad_input in ("",  # No project
                          "x"):  # No task name
            self.assertRaises(BadUsageException, self.cmd.do_t_add, bad_input)

        # Crypto stuff
        tui.addInputAnswers("a Secret passphrase")
        self.cmd.do_t_add("-c x encrypted t1")
        self.assertTrue(self.session.query(Task).get(3).title.startswith(cryptutils.CRYPTO_PREFIX))

    def testRemove(self):
        # Create a recurrent task with one keyword
        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x @kw bla")
        task = self.session.query(Task).one()
        self.cmd.do_t_recurs("1 daily 10:00")

        keyword = self.session.query(Keyword).filter_by(name="kw").one()
        self.assertEqual(keyword.tasks, [task])

        recurrence = self.session.query(Recurrence).one()

        # Pretend we edit the task description so that we have a TaskLock for
        # this task
        taskLockManager = dbutils.TaskLockManager(task)
        taskLockManager.acquire()
        lock = self.session.query(TaskLock).one()

        # Remove it, the keyword should no longer be associated with any task,
        # the recurrence and the lock should be gone
        tui.addInputAnswers("y")
        self.cmd.do_t_remove(str(task.id))

        self.assertEqual(keyword.tasks, [])
        self.assertEqual(list(self.session.query(Recurrence)), [])
        self.assertEqual(list(self.session.query(TaskLock)), [])

        # Should not crash
        taskLockManager.release()

    def testMark(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task = self.session.query(Task).get(1)
        self.assertEqual(task.status, "new")
        self.cmd.do_t_mark_started("1")
        self.assertEqual(task.status, "started")
        self.cmd.do_t_mark_new("1")
        self.assertEqual(task.status, "new")
        self.cmd.do_t_mark_done("1")
        self.assertEqual(task.status, "done")

    def testAddKeywords(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task = self.session.query(Task).get(1)

        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add_keywords("1 @kw1 @kw2=12")

        kwDict = task.getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))

        for bad_input in ("",  # No task
                          "1",  # No keyword
                          "1 kw1"):  # No @ before kw1
            self.assertRaises(YokadiException, self.cmd.do_t_add_keywords, bad_input)

    def testSetProject(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        tui.addInputAnswers("y")
        self.cmd.do_t_project("1 y")
        task1 = self.session.query(Task).get(1)
        self.assertEqual(task1.project.name, "y")

        self.cmd.do_t_add("x t2")
        self.cmd.do_t_project("1 _")
        task1 = self.session.query(Task).get(1)
        self.assertEqual(task1.project.name, "x")

    def testLastTaskId(self):
        # Using "_" with no prior task activity should raise an exception
        self.assertRaises(YokadiException, self.cmd.getTaskFromId, "_")

        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task1 = self.session.query(Task).get(1)
        self.assertEqual(self.cmd.getTaskFromId("_"), task1)

        self.cmd.do_t_add("x t2")
        task2 = self.session.query(Task).get(2)
        self.assertEqual(self.cmd.getTaskFromId("_"), task2)

        self.cmd.do_t_mark_started("1")
        self.assertEqual(self.cmd.getTaskFromId("_"), task1)

    def testLastProjectName(self):
        # Using "_" with no prior project used should raise an exception
        self.assertRaises(YokadiException, self.cmd.do_t_add, "_ t1")
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task1 = self.session.query(Task).get(1)
        self.cmd.do_t_add("_ t2")
        task2 = self.session.query(Task).get(2)
        self.assertEqual(task1.project, task2.project)

    def testRecurs(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task = self.session.query(Task).get(1)
        self.cmd.do_t_recurs("1 daily 10:00")
        desc = str(task.recurrence)
        self.cmd.do_t_recurs("1 weekly FR 23:00")
        self.cmd.do_t_recurs("1 none")
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

        for bad_input in ("",  # No task
                          "1",  # No recurence
                          "1 foo",  # Unknown recurrence
                          "1 daily",  # No time
                          "1 weekly",  # No day
                          "1 weekly monday",  # No time
                          "1 monthly",  # No day
                          "1 monthly 10",  # No time
                          "1 quarterly",  # No day
                          "1 quarterly 10",  # No time
                          "1 monthly foo 12:00",  # Bad date
                          ):
            self.assertRaises(YokadiException, self.cmd.do_t_recurs, bad_input)

    def testTlist(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x @kw1 @kw2=12 t2")

        for line in ("", "-a", "-t", "-d today", "-u 10", "-k %", "-k _%", "-s t", "--overdue",
                     "@%", "@k%", "!@%", "!@kw1", "-f plain", "-f xml", "-f html", "-f csv"):
            self.cmd.do_t_list(line)

    def testNlist(self):
        tui.addInputAnswers("y")
        self.cmd.do_n_add("x t1")
        self.cmd.do_t_add("x t2")
        tui.addInputAnswers("y", "y")
        self.cmd.do_n_add("x @kw1 @kw2=12 t3")
        self.cmd.do_t_add("x @kw1 @kw2=12 t4")

        for line in ("", "-k %", "-k _%", "-s t",
                     "@%", "@k%", "!@%", "!@kw1", "-f plain"):
            self.cmd.do_t_list(line)

    def testTfilter(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x @kw1 @kw2=12 t2")
        tui.addInputAnswers("y")
        self.cmd.do_t_add("y t3")

        for filter in ("@kw1", "x", "x @kw1", "none"):
            self.cmd.do_t_filter(filter)
            out = StringIO()
            oldstdout = sys.stdout
            tui.stdout = out
            self.cmd.do_t_list("")
            self.assertTrue("t2" in out.getvalue())
            if filter in ("x", "none"):
                self.assertTrue("t1" in out.getvalue())
            else:
                self.assertFalse("t1" in out.getvalue())
            if filter == "none":
                self.assertTrue("t3" in out.getvalue())
            else:
                self.assertFalse("t3" in out.getvalue())

            tui.stdout = oldstdout

        self.assertRaises(YokadiException, self.cmd.do_t_filter, "")

    def testTApply(self):
        self.cmd.do_k_add("lala")
        for i in range(10):
            tui.addInputAnswers("y")
            self.cmd.do_t_add("x t%s" % i)
        ids = [1, 2, 4, 5, 6, 9]
        self.cmd.do_t_apply("1 2,4-6 9 t_add_keywords @lala")
        for taskId in range(1, 10):
            kwDict = self.session.query(Task).get(taskId).getKeywordDict()
            if taskId in ids:
                self.assertEqual(kwDict, dict(lala=None))
            else:
                self.assertNotEqual(kwDict, dict(lala=None))

        # raise error if t_list had not been called previously
        self.assertRaises(BadUsageException, self.cmd.do_t_apply, "__ t_add_keywords @toto")

        self.cmd.do_t_list("@lala")
        self.cmd.do_t_apply("__ t_add_keywords @toto")
        for taskId in range(1, 10):
            kwDict = self.session.query(Task).get(taskId).getKeywordDict()
            if taskId in ids:
                self.assertEqual(kwDict, dict(lala=None, toto=None))
            else:
                self.assertNotEqual(kwDict, dict(lala=None, toto=None))

    def testReorder(self):
        self.assertRaises(BadUsageException, self.cmd.do_t_reorder, "unknown_project")
        self.assertRaises(BadUsageException, self.cmd.do_t_reorder, "too much args")

    def testDue(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        for valid_input in ("+1d", "+1m"):
            self.cmd.do_t_due("1 %s" % valid_input)
        for bad_input in ("coucou", "+1s"):
            self.assertRaises(YokadiException, self.cmd.do_t_due, "1 %s" % bad_input)

    def testRemove(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        self.assertEqual(self.session.query(Task).count(), 1)
        tui.addInputAnswers("y")
        self.cmd.do_t_remove("1")
        self.assertEqual(self.session.query(Task).count(), 0)

# vi: ts=4 sw=4 et
