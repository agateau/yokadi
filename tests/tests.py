#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Yokadi unit tests

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import sys
from os.path import dirname, join, pardir
import unittest

sys.path.append(join(dirname(sys.argv[0]), pardir))
import parseutils

gTaskLineToParsedStructList = [
    (u"project some text -k keyword1 -k keyword2=12 some other text", (u"project", u"some text some other text", {u"keyword1":None, u"keyword2":12} )),
    (u"project ééé", (u"project", u"ééé", {} )),
    ]

class ParseUtilsTests(unittest.TestCase):
    def testExtractKeywords(self):
        for src, dst in gTaskLineToParsedStructList:
            result = parseutils.parseTaskLine(src)
            self.assertEqual(result, dst)

    def testCreateTaskLine(self):
        for dummy, parsedStruct in gTaskLineToParsedStructList:
            # We do not check the result of createTaskLine() against the
            # original task line because there are many ways to write the same
            # taskLine.
            taskLine = parseutils.createTaskLine(*parsedStruct)
            result = parseutils.parseTaskLine(taskLine)
            self.assertEqual(result, parsedStruct)


    def testCompleteParameterPosition(self):
        data = [
                 (("bla", "t_add bla", 6, 10), 1),
                 (("bli", "t_add bla bli", 10, 14), 2),
               ]
        for params, expectedResult in data:
            result = parseutils.computeCompleteParameterPosition(*params)
            self.assertEqual(result, expectedResult)



if __name__ == "__main__":
    unittest.main()
# vi: ts=4 sw=4 et
