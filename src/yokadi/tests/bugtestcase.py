# -*- coding: UTF-8 -*-
"""
Bug test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import unittest

import testutils

import tui
from db import Task
from bugcmd import BugCmd

class BugTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        self.cmd = BugCmd()

    def testAdd(self):
        tui.addInputAnswers("y", "2", "4", "123")
        self.cmd.do_bug_add("x t1")

        tasks = list(Task.select())
        result = [x.title for x in tasks]
        expected = [u"t1"]
        self.assertEqual(result, expected)

        kwDict = Task.get(1).getKeywordDict()
        self.assertEqual(kwDict, dict(_severity=2, _likelihood=4, _bug=123))

# vi: ts=4 sw=4 et
