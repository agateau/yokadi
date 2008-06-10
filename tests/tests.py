import sys
import unittest

sys.path.append("..")
import parseutils

gTaskLineToParsedStructList = [
    ("project some text -p property1 -p property2=12 some other text", ("some text some other text", {"p/project":None, "property1":None, "property2":12} )),
    ]

class ParseUtilsTests(unittest.TestCase):
    def testExtractProperties(self):
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



if __name__ == "__main__":
    unittest.main()
# vi: ts=4 sw=4 et
