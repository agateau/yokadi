# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest

import testutils

from yokadi.core import db
from yokadi.core.db import Project, setDefaultConfig
from yokadi.ycli import completers


class CompletersTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        setDefaultConfig()
        self.session = db.getSession()

    def testProjectCompleter(self):
        self.session.add_all([Project(name=u"foo"),
                             Project(name=u"foo2"),
                             Project(name=u"bar")])

        expected = [u"foo ", u"foo2 "]
        completer = completers.ProjectCompleter(1)
        result = completer("f", "t_add f", 6, 8)
        self.assertEqual(result, expected)

    def testCompleteParameterPosition(self):
        data = [
                 (("bla", "t_add bla", 6, 10), 1),
                 (("bli", "t_add bla bli", 10, 14), 2),
               ]
        for params, expectedResult in data:
            result = completers.computeCompleteParameterPosition(*params)
            self.assertEqual(result, expectedResult)
# vi: ts=4 sw=4 et
