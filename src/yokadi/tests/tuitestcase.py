# -*- coding: UTF-8 -*-
"""
TUI module test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import os
import unittest

from ycli import tui

class TuiTestCase(unittest.TestCase):
    def testEditEmptyText(self):
        os.environ["EDITOR"] = "/bin/true"
        out = tui.editText(None)
        self.assertEqual(out, "")
