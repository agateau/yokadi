# -*- coding: UTF-8 -*-
"""
Task test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
import sys
import unittest

import testutils

import dbutils
import tui
from db import Task
from ycli.keywordcmd import KeywordCmd
from yokadiexception import YokadiException

class KeywordTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        tui.clearInputAnswers()
        self.cmd = KeywordCmd()

    def testKEditNoMerge(self):
        t1 = dbutils.addTask("x", "t1", dict(k1=12, k2=None), interactive=False)
        tui.addInputAnswers("newk1")
        self.cmd.do_k_edit("k1")
        kwDict = t1.getKeywordDict()
        self.assert_("k1" not in kwDict)
        self.assertEqual(kwDict.get("newk1"), 12)
        self.assertRaises(YokadiException, dbutils.getKeywordFromName, "k1")

    def testKEditMerge(self):
        t1 = dbutils.addTask("x", "t1", dict(k1=None, k2=None), interactive=False)
        t2 = dbutils.addTask("x", "t2", dict(k1=None), interactive=False)
        tui.addInputAnswers("k2", "y")
        self.cmd.do_k_edit("k1")

        kwDict = t1.getKeywordDict()
        self.assert_("k1" not in kwDict)
        self.assert_("k2" in kwDict)

        kwDict = t2.getKeywordDict()
        self.assert_("k1" not in kwDict)
        self.assert_("k2" in kwDict)

        self.assertRaises(YokadiException, dbutils.getKeywordFromName, "k1")

    def testKEditCannotMerge(self):
        """
        One can't merge keywords if they have different values
        """
        t1 = dbutils.addTask("x", "t1", dict(k1=12, k2=None), interactive=False)
        tui.addInputAnswers("k2", "y")
        self.cmd.do_k_edit("k1")
        kwDict = t1.getKeywordDict()
        self.assert_("k1" in kwDict)
        self.assert_("k2" in kwDict)

        dbutils.getKeywordFromName("k1")
# vi: ts=4 sw=4 et
