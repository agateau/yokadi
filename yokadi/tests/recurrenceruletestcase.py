import unittest

from collections import namedtuple
from datetime import datetime

from dateutil import rrule

from yokadi.core.recurrencerule import RecurrenceRule
from yokadi.core.yokadiexception import YokadiException


# Use a date far away in the future because rrule does not work with dates in
# the past.
# This is a wednesday.
REF_DATE = datetime(2200, 3, 19, 21, 30)

TestRow = namedtuple("TestRow", ("text", "dct", "rule", "nextDate"))

TEST_DATA = [
    TestRow(
        "none",
        {},
        RecurrenceRule(),
        None,
    ),
    TestRow(
        "daily 17:15",
        {"freq": rrule.DAILY, "bymonth": (), "bymonthday": (), "byweekday": (), "byhour": (17,), "byminute": (15,)},
        RecurrenceRule(rrule.DAILY, byhour=17, byminute=15),
        REF_DATE.replace(day=20, hour=17, minute=15)
    ),
    TestRow(
        "weekly monday 10:00",
        {"freq": rrule.WEEKLY, "bymonth": (), "bymonthday": (), "byweekday": (0,), "byhour": (10,), "byminute": (0,)},
        RecurrenceRule(rrule.WEEKLY, byweekday=0, byhour=10),
        REF_DATE.replace(day=24, hour=10, minute=0)
    ),
    TestRow(
        "monthly 2 8:27",
        {"freq": rrule.MONTHLY, "bymonth": (), "bymonthday": (2,), "byweekday": (), "byhour": (8,), "byminute": (27,)},
        RecurrenceRule(rrule.MONTHLY, bymonthday=2, byhour=8, byminute=27),
        REF_DATE.replace(month=4, day=2, hour=8, minute=27)
    ),
    TestRow(
        "quarterly 2 8:27",
        {"freq": rrule.YEARLY, "bymonth": (1, 4, 7, 10), "bymonthday": (2,), "byweekday": (), "byhour": (8,),
         "byminute": (27,)},
        RecurrenceRule(rrule.YEARLY, bymonth=(1, 4, 7, 10), bymonthday=2, byhour=8, byminute=27),
        REF_DATE.replace(month=4, day=2, hour=8, minute=27)
    ),
    TestRow(
        "monthly first wednesday 8:27",
        {"freq": rrule.MONTHLY, "bymonth": (), "bymonthday": (), "byweekday": {"pos": 1, "weekday": 2}, "byhour": (8,),
         "byminute": (27,)},
        RecurrenceRule(rrule.MONTHLY, byweekday=RecurrenceRule.createWeekDay(pos=1, weekday=2), byhour=8, byminute=27),
        REF_DATE.replace(month=4, day=2, hour=8, minute=27)
    ),
    TestRow(
        "monthly last sunday 8:27",
        {"freq": rrule.MONTHLY, "bymonth": (), "bymonthday": (), "byweekday": {"pos": -1, "weekday": 6}, "byhour": (8,),
         "byminute": (27,)},
        RecurrenceRule(rrule.MONTHLY, byweekday=RecurrenceRule.createWeekDay(pos=-1, weekday=6), byhour=8, byminute=27),
        REF_DATE.replace(month=3, day=30, hour=8, minute=27)
    ),
    TestRow(
        "yearly 23/2 8:27",
        {"freq": rrule.YEARLY, "bymonth": (2,), "bymonthday": (23,), "byweekday": (), "byhour": (8,),
         "byminute": (27,)},
        RecurrenceRule(rrule.YEARLY, bymonth=2, bymonthday=23, byhour=8, byminute=27),
        REF_DATE.replace(year=2201, month=2, day=23, hour=8, minute=27)
    ),
]


class RecurrenceRuleTestCase(unittest.TestCase):
    def testFromHumaneString(self):
        testData = [
            ("daily 10:00", RecurrenceRule(rrule.DAILY, byhour=10)),
            ("weekly FR 23:00", RecurrenceRule(rrule.WEEKLY, byweekday=4, byhour=23)),
            ("none", RecurrenceRule()),
            ("weekly fr 23:00", RecurrenceRule(rrule.WEEKLY, byweekday=4, byhour=23)),
            ("weekly Fr 23:00", RecurrenceRule(rrule.WEEKLY, byweekday=4, byhour=23)),
            ("weekly Friday 23:00", RecurrenceRule(rrule.WEEKLY, byweekday=4, byhour=23)),
            ("monthly 3 13:00", RecurrenceRule(rrule.MONTHLY, bymonthday=3, byhour=13)),
            ("monthly second friday 13:00", RecurrenceRule(rrule.MONTHLY,
                                                           byweekday=RecurrenceRule.createWeekDay(weekday=4, pos=2),
                                                           byhour=13)),
            ("yearly 3/07 11:20", RecurrenceRule(rrule.YEARLY, bymonth=7, bymonthday=3, byhour=11, byminute=20)),
            ("quarterly 14 11:20", RecurrenceRule(rrule.YEARLY, bymonth=(1, 4, 7, 10), bymonthday=14, byhour=11,
                                                  byminute=20)),
            ("quarterly first monday 23:20", RecurrenceRule(rrule.YEARLY, bymonth=(1, 4, 7, 10),
                                                            byweekday=RecurrenceRule.createWeekDay(weekday=0, pos=1),
                                                            byhour=23, byminute=20)),
        ] + [(x.text, x.rule) for x in TEST_DATA]

        for text, expected in testData:
            with self.subTest(text=text):
                output = RecurrenceRule.fromHumaneString(text)
                self.assertEqual(output, expected,
                                 '\ninput:    {}\noutput:   {}\nexpected: {}'.format(text, output, expected))

    def testFromHumaneString_badInput(self):
        for badInput in ("foo",  # Unknown recurrence
                         "daily",  # No time
                         "weekly",  # No day
                         "weekly monday",  # No time
                         "monthly",  # No day
                         "monthly 10",  # No time
                         "quarterly",  # No day
                         "quarterly 10",  # No time
                         "monthly foo 12:00",  # Bad date
                         ):
            self.assertRaises(YokadiException, RecurrenceRule.fromHumaneString, badInput)

    def testToFromDict(self):
        for row in TEST_DATA:
            with self.subTest(text=row.text):
                rule = RecurrenceRule.fromDict(row.dct)
                self.assertEqual(rule, row.rule,
                                 '\ninput:    {}\nrule:     {}\nexpected: {}'.format(row.dct, rule, row.rule))
                dct = rule.toDict()
                self.assertEqual(dct, row.dct)

    def testGetNext(self):
        for row in TEST_DATA:
            with self.subTest(text=row.text):
                nextDate = row.rule.getNext(REF_DATE)
                self.assertEqual(nextDate, row.nextDate)
