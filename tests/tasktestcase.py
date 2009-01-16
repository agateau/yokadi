# -*- coding: UTF-8 -*-
"""
Task test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import unittest

import testutils

from db import Project, Task
from taskcmd import TaskCmd

class TaskTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        self.cmd = TaskCmd()

    def testAdd(self):
        project = Project(name="x")
        self.cmd.do_t_add("x t1")
        self.cmd.do_t_add("x t2")

        tasks = list(Task.select())
        result = [x.title for x in tasks]
        expected = [u"t1", u"t2"]
        self.assertEqual(result, expected)
# vi: ts=4 sw=4 et
