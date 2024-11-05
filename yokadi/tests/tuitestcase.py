# -*- coding: UTF-8 -*-
"""
TUI module test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import os
import unittest

from yokadi.ycli import tui


class TuiTestCase(unittest.TestCase):
    def setUp(self):
        tui.clearInputAnswers()

    def testEditEmptyText(self):
        # Add an unused input answer to pass the isInteractive() check in editText()
        tui.addInputAnswers("")

        os.environ["EDITOR"] = "/bin/true"
        out = tui.editText(None)
        self.assertEqual(out, "")

    def testEnterInt(self):
        tui.addInputAnswers("")
        self.assertEqual(tui.enterInt(), None)

        tui.addInputAnswers("a", "12")
        self.assertEqual(tui.enterInt(default=4), 12)

    def testSelectFromList(self):
        lst = [("a", "alpha"), ("b", "bravo"), ("c", "charlie")]
        tui.addInputAnswers("a")
        value = tui.selectFromList(lst, valueForString=str)
        self.assertEqual(value, "a")

        tui.addInputAnswers("z", "b")
        value = tui.selectFromList(lst, valueForString=str)
        self.assertEqual(value, "b")

    def testConfirm(self):
        tui.addInputAnswers("zog", "y")
        value = tui.confirm("bla")
        self.assertTrue(value)

        tui.addInputAnswers("zog", "n")
        value = tui.confirm("bla")
        self.assertFalse(value)
