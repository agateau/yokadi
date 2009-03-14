# -*- coding: UTF-8 -*-
"""
Yokadi parser test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import unittest

from yokadioptionparser import YokadiOptionParser

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
        srcs = ["foo-bar", "foo - bar", "foo -bar", "--bar -f"]
        for src in srcs:
            options, args = parser.parse_args(src)
            # Recreate the line
            line = " ".join(args)
            if src.startswith("-- "):
                src = src[3:]
            self.assertEqual(line, src)

# vi: ts=4 sw=4 et
