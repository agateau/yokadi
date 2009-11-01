# -*- coding: UTF-8 -*-
"""
Alias test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import unittest

import testutils

from db import Config
from aliascmd import AliasCmd

class AliasTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        self.cmd = AliasCmd()


    def testAdd(self):
        self.cmd.do_a_add("l t_list")
        alias = Config.selectBy(name="ALIASES")[0]
        self.assertEqual(eval(alias.value)["l"], "t_list")
