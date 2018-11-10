# -*- coding: UTF-8 -*-
"""
Task test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import unittest

from sqlalchemy.orm.exc import NoResultFound

from yokadi.core import dbutils
from yokadi.ycli import tui
from yokadi.ycli.keywordcmd import KeywordCmd, _listKeywords
from yokadi.core.yokadiexception import YokadiException
from yokadi.core import db


class KeywordTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()
        tui.clearInputAnswers()
        self.cmd = KeywordCmd()

    def testKEditNoMerge(self):
        t1 = dbutils.addTask("x", "t1", dict(k1=12, k2=None), interactive=False)
        tui.addInputAnswers("newk1")
        self.cmd.do_k_edit("k1")
        kwDict = t1.getKeywordDict()
        self.assertTrue("k1" not in kwDict)
        self.assertEqual(kwDict.get("newk1"), 12)
        self.assertRaises(YokadiException, dbutils.getKeywordFromName, "k1")

    def testKEditMerge(self):
        t1 = dbutils.addTask("x", "t1", dict(k1=None, k2=None), interactive=False)
        t2 = dbutils.addTask("x", "t2", dict(k1=None), interactive=False)
        tui.addInputAnswers("k2", "y")
        self.cmd.do_k_edit("k1")

        kwDict = t1.getKeywordDict()
        self.assertTrue("k1" not in kwDict)
        self.assertTrue("k2" in kwDict)

        kwDict = t2.getKeywordDict()
        self.assertTrue("k1" not in kwDict)
        self.assertTrue("k2" in kwDict)

        self.assertRaises(YokadiException, dbutils.getKeywordFromName, "k1")

    def testKEditCannotMerge(self):
        """
        One can't merge keywords if they have different values
        """
        t1 = dbutils.addTask("x", "t1", dict(k1=12, k2=None), interactive=False)
        tui.addInputAnswers("k2", "y")
        self.cmd.do_k_edit("k1")
        kwDict = t1.getKeywordDict()
        self.assertTrue("k1" in kwDict)
        self.assertTrue("k2" in kwDict)

        dbutils.getKeywordFromName("k1")

    def testKRemove(self):
        t1 = dbutils.addTask("x", "t1", dict(k1=12, k2=None), interactive=False)
        tui.addInputAnswers("y")
        self.cmd.do_k_remove("k1")
        kwDict = t1.getKeywordDict()
        self.assertFalse("k1" in kwDict)
        self.assertTrue("k2" in kwDict)
        taskKeyword = self.session.query(db.TaskKeyword).filter_by(taskId=t1.id).one()
        self.assertEqual(taskKeyword.keyword.name, "k2")

    def testKRemove_unused(self):
        self.cmd.do_k_add("kw")
        self.session.query(db.Keyword).filter_by(name="kw").one()
        self.cmd.do_k_remove("kw")
        self.assertRaises(NoResultFound, self.session.query(db.Keyword).filter_by(name="kw").one)

    def testKList(self):
        t1 = dbutils.addTask("x", "t1", dict(k1=12, k2=None), interactive=False)
        t2 = dbutils.addTask("x", "t2", dict(k1=None, k3=None), interactive=False)

        lst = list(_listKeywords(self.session))
        lst = [(name, list(ids)) for name, ids in lst]
        self.assertEqual(lst, [("k1", [t1.id, t2.id]),
                               ("k2", [t1.id]),
                               ("k3", [t2.id]),
                               ])
# vi: ts=4 sw=4 et
