# -*- coding: UTF-8 -*-
"""
Task test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import unittest

import testutils
from mockinputimpl import MockInputImpl

import tui
from db import Project, Task
from taskcmd import TaskCmd

class TaskTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        self.cmd = TaskCmd()

    def testAdd(self):
        inputImpl = MockInputImpl(
            "y", # Create project
            "y", # Create kw1
            "y", # Create kw2
            )
        tui.inputImpl = inputImpl
        self.cmd.do_t_add("x t1")
        self.cmd.do_t_add("x -k kw1 -k kw2=12 t2")

        tasks = list(Task.select())
        result = [x.title for x in tasks]
        expected = [u"t1", u"t2"]
        self.assertEqual(result, expected)

        kwDict = Task.get(2).getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))
# vi: ts=4 sw=4 et
