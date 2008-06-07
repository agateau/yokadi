import sys
import unittest

sys.path.append("..")
import parseutils

class ParseUtilsTests(unittest.TestCase):
    def testExtractProperties(self):
        srcDst = [
            ("some text -p property1 -p property2=12 some other text", ("some text some other text", dict(property1=None, property2=12))),
            ]

        for src, dst in srcDst:
            result = parseutils.extractProperties(src)
            self.assertEqual(result, dst)



if __name__ == "__main__":
    unittest.main()
# vi: ts=4 sw=4 et
