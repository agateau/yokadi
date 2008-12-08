# -*- coding: UTF-8 -*-
import sys
from os.path import dirname, join, pardir
import unittest

sys.path.append(join(dirname(sys.argv[0]), pardir))
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

# vi: ts=4 sw=4 et
