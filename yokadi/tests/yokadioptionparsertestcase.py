# -*- coding: UTF-8 -*-
"""
Yokadi parser test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import unittest

from yokadi.core.yokadioptionparser import YokadiOptionParser
from yokadi.core.yokadiexception import YokadiException


class YokadiOptionParserTestCase(unittest.TestCase):

    def testQuote(self):
        parser = YokadiOptionParser()
        parser.add_argument("cmd", nargs='*')
        src = "There's a quote here"
        args = parser.parse_args(src)
        # Recreate the line
        line = " ".join(args.cmd)
        self.assertEqual(line, src)

    def testDash(self):
        parser = YokadiOptionParser()
        parser.add_argument("cmd", nargs="*")
        srcs = ["foo-bar", "foo - bar"]
        for src in srcs:
            args = parser.parse_args(src)
            # Recreate the line
            line = " ".join(args.cmd)
            self.assertEqual(line, src)

    def testUknownOption(self):
        def parseUnknownOption():
            parser.parse_args("blabla -b")
        parser = YokadiOptionParser()
        self.assertRaises(YokadiException, parseUnknownOption)

# vi: ts=4 sw=4 et
