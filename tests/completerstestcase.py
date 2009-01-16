# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import unittest

import testutils

from db import Project
import completers


class CompletersTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()


    def testProjectCompleter(self):
        Project(name=u"foo")
        Project(name=u"foo2")
        Project(name=u"bar")

        expected = [u"foo", u"foo2"]
        completer = completers.ProjectCompleter(1)
        result = completer("f", "t_add f", 6, 8)
        self.assertEqual(result, expected)

# vi: ts=4 sw=4 et
