# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import unittest

import testutils

from db import Project
from projectcmd import ProjectCmd

class ProjectTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()

    def testRename(self):
        project = Project(name="src")
        id = project.id
        cmd = ProjectCmd()
        cmd.do_p_rename("src dst")
        project = Project.selectBy(id=id)[0]
        self.assertEqual(project.name, "dst")
# vi: ts=4 sw=4 et
