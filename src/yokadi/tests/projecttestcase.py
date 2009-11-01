# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest

import testutils

from db import Project
from projectcmd import ProjectCmd
import tui

class ProjectTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        tui.clearInputAnswers()
        self.cmd = ProjectCmd()


    def testAdd(self):
        tui.addInputAnswers("y")
        self.cmd.do_p_add("p1")

        tui.addInputAnswers("y", "y")
        self.cmd.do_p_add("p2 @kw1 @kw2=12")

        projects = list(Project.select())
        result = [x.name for x in projects]
        expected = [u"p1", u"p2"]
        self.assertEqual(result, expected)

        kwDict = Project.get(2).getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))

# vi: ts=4 sw=4 et
