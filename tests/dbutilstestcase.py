# -*- coding: UTF-8 -*-
"""
Date utilities test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import unittest

import testutils

import dbutils
import tui
from db import Keyword, Project


class DbUtilsTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()


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
