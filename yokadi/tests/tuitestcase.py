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
    def testEditEmptyText(self):
        os.environ["EDITOR"] = "/bin/true"
        out = tui.editText(None)
        self.assertEqual(out, "")
