# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import unittest

import testutils

from yokadi.core import db, dbutils
from yokadi.core.db import Project, Keyword, Task
from yokadi.core.yokadiexception import YokadiException
from yokadi.ycli.main import YokadiCmd
from yokadi.ycli import tui


class ProjectTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()
        tui.clearInputAnswers()
        self.cmd = YokadiCmd()

    def testAdd(self):
        tui.addInputAnswers("y")
        self.cmd.do_p_add("p1")
        self.cmd.do_p_add("p2")

        projects = self.session.query(Project).all()
        result = [x.name for x in projects]
        expected = ["p1", "p2"]
        self.assertEqual(result, expected)

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
        # Create project p1 with one associated task
        tui.addInputAnswers("y")
        self.cmd.do_p_add("p1")
        project = self.session.query(Project).one()
        task = dbutils.addTask("p1", "t1", interactive=False)
        taskId = task.id

        # Remove project, its task should be removed
        tui.addInputAnswers("y")
        self.cmd.do_p_remove("p1")

        self.assertEqual(list(self.session.query(Task).filter_by(id=taskId)), [])

    def testStatus(self):
        # Create project p1 and test set active and set inactive method
        self.cmd.do_p_add("p1")
        project = self.session.query(Project).filter_by(id=1).one()
        self.assertEqual(project.name, "p1")

        self.assertEqual(project.active, True)
        self.cmd.do_p_set_inactive("p1")
        self.assertEqual(project.active, False)
        self.cmd.do_p_set_active("p1")
        self.assertEqual(project.active, True)

# vi: ts=4 sw=4 et
