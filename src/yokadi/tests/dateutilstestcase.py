# -*- coding: UTF-8 -*-
"""
Date utilities test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import unittest
from datetime import datetime, timedelta
 
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


    def testParseDateTimeDelta(self):
        testData = [
            ("1m", timedelta(minutes=1)),
            ("3M", timedelta(minutes=3)),
            ("5H", timedelta(hours=5)),
            ("6.5D", timedelta(days=6, hours=12)),
            ("12W", timedelta(days=12*7)),
            ]

        for text, expected in testData:
            output = dateutils.parseDateTimeDelta(text)
            self.assertEquals(expected, output)


    def testParseHumaneDateTime(self):        
        for date in ("+5M", "+1m", "+2H", "+3h", "+9D", "+14d", "+432W", "+0w",
                     "01/01/2009", "10/10/2008 12", "7/7/2007 10:15", "1/2/2003 1:2:3"):
            dateutils.parseHumaneDateTime(date)
            
        for invalidDate in ("2008", "01/2009", "01//02/01", "02/20/2009", "", "-23d", "+3e", "lkjljlkjlkj", "200/200/2009"):
            self.assertRaises(YokadiException, dateutils.parseHumaneDateTime, invalidDate)

        # Fake today to a fixed date. This is a saturday (weekday=5).
        today = datetime(2009, 1, 3)
        testData = [
            ("06/02/2009", datetime(2009, 2, 6)),
            ("06/02/2009 12:30", datetime(2009, 2, 6, 12, 30)),
            ("tomorrow 18:00", today + timedelta(days=1, hours=18)),
            ("sunday", datetime(2009, 1, 4)),
            ("tu 11:45", datetime(2009, 1, 6, 11, 45)),
            ]

        for text, expected in testData:
            output = dateutils.parseHumaneDateTime(text, today=today)
            self.assertEquals(expected, output)


    def testFormatTimeDelta(self):
        testData = [
            (timedelta(minutes=1), "1m"),
            (timedelta(days=2, hours=5), "2d"),
            (timedelta(days=12*7), "12w"),
            ]

        for input, expected in testData:
            output = dateutils.formatTimeDelta(input)
            self.assertEquals(expected, output)
            output = dateutils.formatTimeDelta(-input)
            self.assertEquals("-" + expected, output)
# vi: ts=4 sw=4 et
