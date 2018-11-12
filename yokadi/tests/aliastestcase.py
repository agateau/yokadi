# -*- coding: UTF-8 -*-
"""
Alias test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""
import unittest

from contextlib import redirect_stdout
from io import StringIO


from yokadi.core import db
from yokadi.core.db import Alias
from yokadi.ycli.aliascmd import AliasCmd
from yokadi.ycli import colors
from yokadi.ycli import tui


class AliasTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()
        self.cmd = AliasCmd()

    def testList(self):
        self.cmd.do_a_add("b t_add")
        self.cmd.do_a_add("a t_list")
        out = StringIO()
        with redirect_stdout(out):
            self.cmd.do_a_list("")
            content = out.getvalue()
            self.assertEqual(content,
                             colors.BOLD + "a".ljust(10) + colors.RESET + "=> t_list\n"
                             + colors.BOLD + "b".ljust(10) + colors.RESET + "=> t_add\n")

    def testList_empty(self):
        out = StringIO()
        with redirect_stdout(out):
            self.cmd.do_a_list("")
            content = out.getvalue()
            self.assertTrue("No alias defined" in content)

    def testAdd(self):
        self.cmd.do_a_add("l t_list")
        self.cmd.do_a_add("la t_list -a")
        aliases = Alias.getAsDict(self.session)
        self.assertEqual(aliases["l"], "t_list")
        self.cmd.do_a_remove("l")
        self.cmd.do_a_remove("la")
        self.cmd.do_a_remove("unknown")
        aliases = Alias.getAsDict(self.session)
        self.assertEqual(aliases, {})

    def testEditName(self):
        self.cmd.do_a_add("l t_list")

        tui.addInputAnswers("ls")
        self.cmd.do_a_edit_name("l")

        aliases = Alias.getAsDict(self.session)
        self.assertEqual(aliases["ls"], "t_list")

    def testEditCommand(self):
        self.cmd.do_a_add("l t_list")

        tui.addInputAnswers("foo")
        self.cmd.do_a_edit_command("l")

        aliases = Alias.getAsDict(self.session)
        self.assertEqual(aliases["l"], "foo")
