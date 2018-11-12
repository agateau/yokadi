# -*- coding: UTF-8 -*-
"""
Help test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os
import sys
import unittest

from cmd import Cmd
from contextlib import contextmanager

from yokadi.core import db
from yokadi.ycli.main import YokadiCmd


@contextmanager
def to_devnull(out):
    out_fd = out.fileno()
    with open(os.devnull, "wb") as null, \
            os.fdopen(os.dup(out_fd), "wb") as copied:
        out.flush()
        os.dup2(null.fileno(), out_fd)
        try:
            yield
        finally:
            out.flush()
            os.dup2(copied.fileno(), out_fd)


class HelpTestCase(unittest.TestCase):
    """
    A basic test for the command helps: it just execute 'help <cmd>' on all
    commands. This catches invalid format characters in the help strings.
    """
    def setUp(self):
        # Some help commands look into the db for default values
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()

    def testHelp(self):
        cmd = YokadiCmd()
        for attr in dir(cmd):
            if not attr.startswith("do_"):
                continue

            yokadiCommand = attr[3:]
            try:
                # Execute the command, but redirect stdout and stderr to
                # /dev/null to avoid flooding the terminal
                with to_devnull(sys.stdout), to_devnull(sys.stderr):
                    # We use Cmd implementation of onecmd() because YokadiCmd
                    # overrides it to catch exceptions
                    Cmd.onecmd(cmd, "help " + yokadiCommand)
            except Exception:
                print("'help %s' failed" % yokadiCommand)
                raise

# vi: ts=4 sw=4 et
