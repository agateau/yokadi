# encoding: utf-8
import sys
import unittest

sys.path.append("..")
import parseutils

gTaskLineToParsedStructList = [
    ("project some text -k keyword1 -k keyword2=12 some other text", ("project", "some text some other text", {"keyword1":None, "keyword2":12} )),
    ("project ééé", ("project", "ééé", {} )),
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
