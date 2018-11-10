# -*- coding: UTF-8 -*-
"""
Parser utilities test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import unittest
from yokadi.ycli import parseutils

gTaskLineToParsedStructList = [
    ("project some text @keyword1 @keyword2=12 some other text", ("project", "some text some other text",
                                                                  {"keyword1": None, "keyword2": 12})),
    ("project ééé", ("project", "ééé", {})),
    ("project let's include quotes\"", ("project", "let's include quotes\"", {})),
    ("   project this  one has  extra spaces  ", ("project", "this one has extra spaces", {})),
]


class ParseUtilsTestCase(unittest.TestCase):
    def testExtractKeywords(self):
        for src, dst in gTaskLineToParsedStructList:
            result = parseutils.parseLine(src)
            self.assertEqual(result, dst)

    def testCreateLine(self):
        for dummy, parsedStruct in gTaskLineToParsedStructList:
            # We do not check the result of createLine() against the
            # original task line because there are many ways to write the same
            # taskLine.
            taskLine = parseutils.createLine(*parsedStruct)
            result = parseutils.parseLine(taskLine)
            self.assertEqual(result, parsedStruct)
