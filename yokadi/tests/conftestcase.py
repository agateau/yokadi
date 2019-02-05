# -*- coding: UTF-8 -*-
"""
Alias test cases
@author: Benjamin Port <benjamin.port@ben2367.fr>
@license: GPL v3 or later
"""

import unittest
import sys
from io import StringIO

from yokadi.core import db
from yokadi.core.db import setDefaultConfig
from yokadi.core.yokadiexception import YokadiException
from yokadi.ycli import tui
from yokadi.ycli.main import YokadiCmd


class ConfTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        setDefaultConfig()
        self.session = db.getSession()
        tui.clearInputAnswers()
        self.cmd = YokadiCmd()

    def testConfig(self):
        out = StringIO()
        oldstdout = sys.stdout
        tui.stdout = out
        self.cmd.do_c_set("ALARM_DELAY 69")
        self.cmd.do_c_get("ALARM_DELAY")
        self.assertTrue("ALARM_DELAY" in out.getvalue())
        self.assertTrue("69" in out.getvalue())
        tui.stdout = oldstdout

    def testPositiveValueConfig(self):
        self.assertRaises(YokadiException, self.cmd.do_c_set, "ALARM_DELAY -1")
        self.assertRaises(YokadiException, self.cmd.do_c_set, "ALARM_SUSPEND -1")
        self.assertRaises(YokadiException, self.cmd.do_c_set, "PURGE_DELAY -1")

    def testWrongKey(self):
        self.assertRaises(YokadiException, self.cmd.do_c_set, "BAD_KEY value")
        self.assertRaises(YokadiException, self.cmd.do_c_get, "BAD_KEY")
