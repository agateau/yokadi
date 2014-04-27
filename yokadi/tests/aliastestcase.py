# -*- coding: UTF-8 -*-
"""
Alias test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import unittest

import testutils

from yokadi.core.db import Config, DBHandler
from yokadi.ycli.aliascmd import AliasCmd


class AliasTestCase(unittest.TestCase):
    def setUp(self):
        DBHandler.connectDatabase("", memoryDatabase=True)
        self.session = DBHandler.getSession()
        self.cmd = AliasCmd()

    def testAdd(self):
        self.cmd.do_a_add("l t_list")
        self.cmd.do_a_add("la t_list -a")
        alias = self.session.query(Config).filter_by(name="ALIASES")[0]
        self.assertEqual(eval(alias.value)["l"], "t_list")
        self.cmd.do_a_remove("l")
        self.cmd.do_a_remove("la")
        self.cmd.do_a_remove("unknown")
        self.assertEqual(eval(alias.value), {})
