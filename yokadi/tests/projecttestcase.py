# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest

import testutils

from yokadi.core import db
from yokadi.core.db import Project
from yokadi.core.yokadiexception import YokadiException
from yokadi.ycli.projectcmd import ProjectCmd
from yokadi.ycli import tui


class ProjectTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()
        tui.clearInputAnswers()
        self.cmd = ProjectCmd()

    def testAdd(self):
        tui.addInputAnswers("y")
        self.cmd.do_p_add(u"p1")

        tui.addInputAnswers("y", "y")
        self.cmd.do_p_add(u"p2 @kw1 @kw2=12")

        projects = self.session.query(Project).all()
        result = [x.name for x in projects]
        expected = [u"p1", u"p2"]
        self.assertEqual(result, expected)

        kwDict = self.session.query(Project).filter_by(id=2).one().getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))

    def testEdit(self):
        # Create project p1 and rename it to p2
        self.cmd.do_p_add(u"p1")
        project = self.session.query(Project).filter_by(id=1).one()
        self.assertEqual(project.name, u"p1")

        tui.addInputAnswers("p2")
        self.cmd.do_p_edit(u"p1")
        self.assertEqual(project.name, u"p2")

        # Create project p3 and try to rename it to p2
        self.cmd.do_p_add(u"p3")
        project = self.session.query(Project).filter_by(name=u"p3").one()
        self.assertEqual(project.name, u"p3")

        tui.addInputAnswers(u"p2")
        self.assertRaises(YokadiException, self.cmd.do_p_edit, u"p3")
        self.assertEqual(project.name, u"p3")

# vi: ts=4 sw=4 et
