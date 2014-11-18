# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest

import testutils

from yokadi.core import db, dbutils
from yokadi.core.db import Project, Keyword, Task
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
        self.cmd.do_p_add("p1")

        tui.addInputAnswers("y", "y")
        self.cmd.do_p_add("p2 @kw1 @kw2=12")

        projects = self.session.query(Project).all()
        result = [x.name for x in projects]
        expected = ["p1", "p2"]
        self.assertEqual(result, expected)

        kwDict = self.session.query(Project).filter_by(id=2).one().getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))

    def testEdit(self):
        # Create project p1 and rename it to p2
        self.cmd.do_p_add("p1")
        project = self.session.query(Project).filter_by(id=1).one()
        self.assertEqual(project.name, "p1")

        tui.addInputAnswers("p2")
        self.cmd.do_p_edit("p1")
        self.assertEqual(project.name, "p2")

        # Create project p3 and try to rename it to p2
        self.cmd.do_p_add("p3")
        project = self.session.query(Project).filter_by(name="p3").one()
        self.assertEqual(project.name, "p3")

        tui.addInputAnswers("p2")
        self.assertRaises(YokadiException, self.cmd.do_p_edit, "p3")
        self.assertEqual(project.name, "p3")

    def testRemove(self):
        # Create project p1, with one project keyword and one associated task
        tui.addInputAnswers("y")
        self.cmd.do_p_add("p1 @kw")
        project = self.session.query(Project).one()
        task = dbutils.addTask("p1", "t1", interactive=False)
        taskId = task.id

        keyword = self.session.query(Keyword).filter_by(name="kw").one()
        self.assertEqual(keyword.projects, [project])

        # Remove project, its task should be removed and the created keyword
        # should no longer be associated with any project
        tui.addInputAnswers("y")
        self.cmd.do_p_remove("p1")

        self.assertEqual(keyword.projects, [])

        self.assertEqual(list(self.session.query(Task).filter_by(id=taskId)), [])

# vi: ts=4 sw=4 et
