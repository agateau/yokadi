# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os
import json

import testutils

from yokadi.core import db, dbutils
from yokadi.core.db import Project, Task
from yokadi.core.yokadiexception import YokadiException
from yokadi.sync import dump
from yokadi.ycli.main import YokadiCmd
from yokadi.ycli import tui
from yokadi.tests.yokaditestcase import YokadiTestCase


class ProjectTestCase(YokadiTestCase):
    def setUp(self):
        YokadiTestCase.setUp(self)
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

    def testMerge(self):
        COUNT = 4
        for x in range(COUNT):
            dbutils.addTask('p1', 'p1-t{}'.format(x), interactive=False)
            dbutils.addTask('p2', 'p2-t{}'.format(x), interactive=False)

        # Merge p1 into p2
        tui.addInputAnswers("y")
        self.cmd.do_p_merge("p1 p2")

        # p2 should have both its tasks and all p1 tasks now
        project = self.session.query(Project).filter_by(name="p2").one()
        tasks = set([x.title for x in project.tasks])

        expected = set()
        for x in range(COUNT):
            expected.add('p1-t{}'.format(x))
            expected.add('p2-t{}'.format(x))
        self.assertEqual(tasks, expected)

        # p1 should be gone
        testutils.assertQueryEmpty(self, self.session.query(Project).filter_by(name="p1"))

    def testMergeItselfFails(self):
        project = Project(name="p1")
        self.assertRaises(YokadiException, project.merge, self.session, project)

    def testProjectMergeUpdatesDump(self):
        self.cmd.do_s_init("")
        t1 = dbutils.addTask("p1", "t1", interactive=False)
        t2 = dbutils.addTask("p2", "t2", interactive=False)
        self.session.commit()

        # Merge p1 into p2
        p1 = dbutils.getProject(self.session, name="p1")
        p2 = dbutils.getProject(self.session, name="p2")
        p2.merge(self.session, p1)
        self.session.commit()

        # Check dumps
        for task in t1, t2:
            path = os.path.join(self.cmd.dumpDir, dump.pathForObject(task))
            with open(path) as fp:
                dct = json.load(fp)
            self.assertEqual(dct["projectUuid"], p2.uuid)

        p1path = os.path.join(self.cmd.dumpDir, dump.pathForObject(p1))
        self.assertFalse(os.path.exists(p1path), "dump file for porject p1 should be gone")


# vi: ts=4 sw=4 et
