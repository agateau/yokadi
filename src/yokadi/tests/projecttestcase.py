# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest

import testutils

from yokadi.core.db import Project
from yokadi.core.yokadiexception import YokadiException
from yokadi.ycli.projectcmd import ProjectCmd
from yokadi.ycli import tui

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

    def testEdit(self):
        # Create project p1 and rename it to p2
        self.cmd.do_p_add("p1")
        project = Project.get(1)
        self.assertEqual(project.name, "p1")

        tui.addInputAnswers("p2")
        self.cmd.do_p_edit("p1")
        self.assertEqual(project.name, "p2")

        # Create project p3 and try to rename it to p2
        self.cmd.do_p_add("p3")
        project = Project.get(2)
        self.assertEqual(project.name, "p3")

        tui.addInputAnswers("p2")
        self.assertRaises(YokadiException, self.cmd.do_p_edit, "p3")
        self.assertEqual(project.name, "p3")

# vi: ts=4 sw=4 et
