# -*- coding: UTF-8 -*-
"""
Parser utilities test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest
import parseutils

gTaskLineToParsedStructList = [
    (u"project some text @keyword1 @keyword2=12 some other text", (u"project", u"some text some other text", {u"keyword1":None, u"keyword2":12} )),
    (u"project ééé", (u"project", u"ééé", {} )),
    (u"project let's include quotes\"", (u"project", u"let's include quotes\"", {} )),
    (u"   project this  one has  extra spaces  ", (u"project", u"this one has extra spaces", {} )),
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
