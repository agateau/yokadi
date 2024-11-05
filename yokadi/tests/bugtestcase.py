# -*- coding: UTF-8 -*-
"""
Bug test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import unittest

from yokadi.ycli import tui
from yokadi.ycli.main import YokadiCmd
from yokadi.core import db, dbutils
from yokadi.core.db import Task, setDefaultConfig
from yokadi.core.yokadiexception import YokadiException


class BugTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()
        setDefaultConfig()
        tui.clearInputAnswers()
        self.cmd = YokadiCmd()

    def testAdd(self):
        tui.addInputAnswers("y", "2", "4", "123")
        self.cmd.do_bug_add("x t1")

        tui.addInputAnswers("n")
        self.cmd.do_bug_add("notExistingProject newBug")

        tasks = self.session.query(Task).all()
        result = [x.title for x in tasks]
        expected = ["t1"]
        self.assertEqual(result, expected)

        kwDict = self.session.get(Task, 1).getKeywordDict()
        self.assertEqual(kwDict, dict(_severity=2, _likelihood=4, _bug=123))

        for bad_input in ("",  # No project
                          "x"):  # No task name
            self.assertRaises(YokadiException, self.cmd.do_bug_add, bad_input)

    def testEdit(self):
        task = dbutils.addTask("prj", "bug", interactive=False)
        kwDict = dict(_severity=1, _likelihood=2, _bug=3)
        task.setKeywordDict(kwDict)
        self.session.commit()

        tui.addInputAnswers("bug edited", "2", "4", "6")
        self.cmd.do_bug_edit(str(task.id))

        task = dbutils.getTaskFromId(task.id)
        self.assertEqual(task.title, "bug edited")
        kwDict = task.getKeywordDict()
        self.assertEqual(kwDict, dict(_severity=2, _likelihood=4, _bug=6))

# vi: ts=4 sw=4 et
