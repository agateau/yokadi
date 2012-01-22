# -*- coding: UTF-8 -*-
"""
Yokadi parser test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest

from core.yokadioptionparser import YokadiOptionParser
from core.yokadiexception import YokadiException


class YokadiOptionParserTestCase(unittest.TestCase):
    def testEmptyLine(self):
        parser = YokadiOptionParser()
        options, args = parser.parse_args(u'')
        self.assertEqual(args, [])

    def testQuote(self):
        parser = YokadiOptionParser()
        src = u"There's a quote here"
        options, args = parser.parse_args(src)
        # Recreate the line
        line = " ".join(args)
        self.assertEqual(line, src)

    def testDash(self):
        parser = YokadiOptionParser()
        srcs = ["foo-bar", "foo - bar"]
        for src in srcs:
            options, args = parser.parse_args(src)
            # Recreate the line
            line = " ".join(args)
            self.assertEqual(line, src)

    def testUknownOption(self):
        def parseUnknownOption():
            parser.parse_args("blabla -b")
        parser = YokadiOptionParser()
        self.assertRaises(YokadiException, parseUnknownOption)

# vi: ts=4 sw=4 et
