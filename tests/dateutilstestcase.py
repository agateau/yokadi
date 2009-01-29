# -*- coding: UTF-8 -*-
"""
Date utilities test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPLv3
"""

import unittest
from datetime import datetime
 
import dateutils
from yokadiexception import YokadiException 

class DateUtilsTestCase(unittest.TestCase):
    def testGuessDateFormat(self):
        testData = [
            ("06/02/2009", "%d/%m/%Y"),
            ("06/02", "%d/%m"),
            ]

        for text, expected in testData:
            output = dateutils.guessDateFormat(text)
            self.assertEquals(expected, output)


    def testParseHumaneDateTime(self):        
        for date in ("+5M", "+1m", "+2H", "+3h", "+9D", "+14d", "+432W", "+0w",
                     "01/01/2009", "10/10/2008 12", "7/7/2007 10:15", "1/2/2003 1:2:3"):
            dateutils.parseHumaneDateTime(date)
            
        for invalidDate in ("2008", "01/2009", "01//02/01", "02/20/2009", "", "-23d", "+3e", "lkjljlkjlkj"):
            self.assertRaises(YokadiException, dateutils.parseHumaneDateTime, invalidDate)

        testData = [
            ("06/02/2009", datetime(2009, 2, 6)),
            ("06/02/2009 12:30", datetime(2009, 2, 6, 12, 30)),
            ]

        for text, expected in testData:
            output = dateutils.parseHumaneDateTime(text)
            self.assertEquals(expected, output)
# vi: ts=4 sw=4 et
