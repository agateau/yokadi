# -*- coding: UTF-8 -*-
"""
Date utilities test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import unittest
import operator
from datetime import datetime, timedelta

import ydateutils
from yokadiexception import YokadiException

class YDateUtilsTestCase(unittest.TestCase):
    def testGuessDateFormat(self):
        testData = [
            ("06/02/2009", "%d/%m/%Y"),
            ("06/02", "%d/%m"),
            ]

        for text, expected in testData:
            output = ydateutils.guessDateFormat(text)
            self.assertEquals(expected, output)


    def testParseDateTimeDelta(self):
        testData = [
            ("1m", timedelta(minutes=1)),
            ("3M", timedelta(minutes=3)),
            ("5H", timedelta(hours=5)),
            ("6.5D", timedelta(days=6, hours=12)),
            ("12W", timedelta(days=12 * 7)),
            ]

        for text, expected in testData:
            output = ydateutils.parseDateTimeDelta(text)
            self.assertEquals(expected, output)


    def testParseHumaneDateTime(self):
        for date in ("+5M", "+1m", "+2H", "+3h", "+9D", "+14d", "+432W", "+0w",
                     "01/01/2009", "10/10/2008 12", "7/7/2007 10:15", "1/2/2003 1:2:3"):
            ydateutils.parseHumaneDateTime(date)

        for invalidDate in ("2008", "01/2009", "01//02/01", "02/20/2009", "", "+3e", "lkjljlkjlkj", "200/200/2009"):
            self.assertRaises(YokadiException, ydateutils.parseHumaneDateTime, invalidDate)

        # Fake today to a fixed date. This is a saturday (weekday=5).
        today = datetime(2009, 1, 3)
        endOfDay = dict(hour=23, minute=59, second=59)
        startOfDay = dict(hour=0, minute=0, second=0)
        testData = [
            ("06/02/2009",       None,                       datetime(2009, 2, 6)),
            ("06/02/2009 12:30", None,                       datetime(2009, 2, 6, 12, 30)),
            ("06/02/2009",       ydateutils.TIME_HINT_BEGIN, datetime(2009, 2, 6, 0, 0, 0)),
            ("06/02/2009",       ydateutils.TIME_HINT_END,   datetime(2009, 2, 6, 23, 59, 59)),
            ("tomorrow 18:00",   None,                       today + timedelta(days=1, hours=18)),
            ("tomorrow",         ydateutils.TIME_HINT_END,   today.replace(day=4, hour=23, minute=59, second=59)),
            ("sunday",           None,                       datetime(2009, 1, 4)),
            ("tu 11:45",         None,                       datetime(2009, 1, 6, 11, 45)),
            ("today",            ydateutils.TIME_HINT_END,   today.replace(**endOfDay)),
            ("today",            ydateutils.TIME_HINT_BEGIN, today.replace(**startOfDay)),
            ("now",              None,                       today),
            ("+2w",              None,                       datetime(2009, 1, 17)),
            ("+1d",              None,                       datetime(2009, 1, 4)),
            ("-1d",              None,                       datetime(2009, 1, 2)),
            ("+3h",              None,                       datetime(2009, 1, 3, 3, 0)),
            ("-1M",              None,                       datetime(2009, 1, 2, 23, 59)),
            ]

        for text, hint, expected in testData:
            output = ydateutils.parseHumaneDateTime(text, hint=hint, today=today)
            self.assertEquals(expected, output)


    def testFormatTimeDelta(self):
        testData = [
            (timedelta(minutes=1), "1m"),
            (timedelta(days=2, hours=5), "2d"),
            (timedelta(days=12 * 7), "12w"),
            ]

        for input, expected in testData:
            output = ydateutils.formatTimeDelta(input)
            self.assertEquals(expected, output)
            output = ydateutils.formatTimeDelta(-input)
            self.assertEquals("-" + expected, output)


    def testParseDateLimit(self):
        # Fake today to a fixed date. This is a saturday (weekday=5).
        today = datetime(2009, 1, 3)
        endOfDay = dict(hour=23, minute=59, second=59)
        startOfDay = dict(hour=0, minute=0, second=0)

        testData = [
            ("today",          operator.__le__, today.replace(**endOfDay)                  ),
            ("<=today",        operator.__le__, today.replace(**endOfDay)                  ),
            ("<today",         operator.__lt__, today.replace(**startOfDay)                ),
            (">today",         operator.__gt__, today.replace(**endOfDay)                  ),
            (">=today",        operator.__ge__, today.replace(**startOfDay)                ),
            ("<=06/02/2009",   operator.__le__, datetime(2009, 2, 6).replace(**endOfDay)   ),
            ("<06/02/2009",    operator.__lt__, datetime(2009, 2, 6).replace(**startOfDay) ),
            ("tomorrow 18:00", operator.__le__, today + timedelta(days=1, hours=18)        ),
            ("sunday",         operator.__le__, datetime(2009, 1, 4).replace(**endOfDay)   ),
            ("tu 11:45",       operator.__le__, datetime(2009, 1, 6, 11, 45)               ),
            ]

        for text, expectedOp, expectedDate in testData:
            output = ydateutils.parseDateLimit(text, today=today)
            output = ydateutils.parseDateLimit(text, today=today)
            self.assertEquals(expectedOp, output[0])
            self.assertEquals(expectedDate, output[1])

# vi: ts=4 sw=4 et
