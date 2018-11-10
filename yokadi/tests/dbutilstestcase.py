# -*- coding: UTF-8 -*-
"""
Date utilities test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import unittest

from datetime import datetime

from yokadi.core import dbutils, db
from yokadi.ycli import tui
from yokadi.core.db import Keyword, Project
from yokadi.core.yokadiexception import YokadiException


class DbUtilsTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()
        tui.clearInputAnswers()

    def testGetTaskFromId(self):
        tui.addInputAnswers("y")
        t1 = dbutils.addTask("x", "t1", {})

        task = dbutils.getTaskFromId(str(t1.id))
        self.assertEqual(task, t1)

        task = dbutils.getTaskFromId(t1.id)
        self.assertEqual(task, t1)

        task = dbutils.getTaskFromId(t1.uuid)
        self.assertEqual(task, t1)

    def testGetOrCreateKeyword(self):
        # interactive
        tui.addInputAnswers("y")
        dbutils.getOrCreateKeyword("k1")
        self.session.query(Keyword).filter_by(name="k1").one()

        # !interactive
        dbutils.getOrCreateKeyword("k2", interactive=False)
        self.session.query(Keyword).filter_by(name="k2").one()

    def testGetOrCreateProject(self):
        # interactive
        tui.addInputAnswers("y")
        dbutils.getOrCreateProject("p1")
        self.session.query(Project).filter_by(name="p1").one()

        # !interactive
        dbutils.getOrCreateProject("p2", interactive=False)
        self.session.query(Project).filter_by(name="p2").one()

    def testGetKeywordFromName(self):
        tui.addInputAnswers("y")
        k1 = dbutils.getOrCreateKeyword("k1", self.session)
        self.assertRaises(YokadiException, dbutils.getKeywordFromName, "")
        self.assertRaises(YokadiException, dbutils.getKeywordFromName, "foo")
        self.assertEqual(k1, dbutils.getKeywordFromName("k1"))

    def testTaskLockManagerStaleLock(self):
        tui.addInputAnswers("y")
        t1 = dbutils.addTask("x", "t1", {})
        taskLockManager = dbutils.TaskLockManager(t1)

        # Lock the task
        taskLockManager.acquire(pid=1, now=datetime(2014, 1, 1))
        lock1 = taskLockManager._getLock()
        self.assertEqual(lock1.pid, 1)

        # Try to lock again, the stale lock should get reused
        taskLockManager.acquire(pid=2, now=datetime(2015, 1, 1))
        lock2 = taskLockManager._getLock()
        self.assertEqual(lock1.id, lock2.id)
        self.assertEqual(lock2.pid, 2)

# vi: ts=4 sw=4 et
