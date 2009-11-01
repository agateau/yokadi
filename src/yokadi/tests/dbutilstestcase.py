# -*- coding: UTF-8 -*-
"""
Date utilities test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest

import testutils

import dbutils
import tui
from db import Keyword, Project
from yokadiexception import YokadiException


class DbUtilsTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        tui.clearInputAnswers()


    def testGetTaskFromId(self):
        tui.addInputAnswers("y")
        t1 = dbutils.addTask("x", "t1", {})

        task = dbutils.getTaskFromId(str(t1.id))
        self.assertEquals(task, t1)


    def testGetOrCreateKeyword(self):
        # interactive
        tui.addInputAnswers("y")
        dbutils.getOrCreateKeyword("k1")
        self._assertOneObject(Keyword.selectBy(name="k1"))

        # !interactive
        dbutils.getOrCreateKeyword("k2", interactive=False)
        self._assertOneObject(Keyword.selectBy(name="k2"))


    def testGetOrCreateProject(self):
        # interactive
        tui.addInputAnswers("y")
        dbutils.getOrCreateProject("p1")
        self._assertOneObject(Project.selectBy(name="p1"))

        # !interactive
        dbutils.getOrCreateProject("p2", interactive=False)
        self._assertOneObject(Project.selectBy(name="p2"))


    def _assertOneObject(self, result):
        self.assertEquals(len(list(result)), 1)
# vi: ts=4 sw=4 et
