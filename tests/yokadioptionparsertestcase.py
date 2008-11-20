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

# vi: ts=4 sw=4 et
