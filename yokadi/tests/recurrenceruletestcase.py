import unittest

from datetime import datetime

from dateutil import rrule

from yokadi.core.recurrencerule import RecurrenceRule
from yokadi.core.yokadiexception import YokadiException


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
            ("monthly second friday 13:00", RecurrenceRule(rrule.MONTHLY, byweekday=rrule.weekday(4, 2), byhour=13)),
            ("yearly 3/07 11:20", RecurrenceRule(rrule.YEARLY, bymonth=7, bymonthday=3, byhour=11, byminute=20)),
            ("quarterly 14 11:20", RecurrenceRule(rrule.YEARLY, bymonth=(1, 4, 7, 10), bymonthday=14, byhour=11, byminute=20)),
            ("quarterly first monday 23:20", RecurrenceRule(rrule.YEARLY, bymonth=(1, 4, 7, 10), byweekday=rrule.weekday(0, 1), byhour=23, byminute=20)),
            ]

        for text, expected in testData:
            output = RecurrenceRule.fromHumaneString(text)
            self.assertEqual(output, expected,
                '\ninput:    {}\noutput:   {}\nexpected: {}'.format(text, output, expected)
            )

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

    def testFromDict(self):
        testData = [
            (
                {},
                RecurrenceRule()
            ),
            (
                {"bymonth": None, "byminute": (0,), "byhour": (10,), "byweekday": (0,), "bymonthday": (), "freq": rrule.WEEKLY},
                RecurrenceRule(rrule.WEEKLY, byweekday=0, byhour=10)
            ),
            (
                {"bymonth": (2,), "byminute": (27,), "byhour": (8,), "byweekday": None, "bymonthday": (23,), "freq": rrule.YEARLY},
                RecurrenceRule(rrule.YEARLY, bymonth=2, bymonthday=23, byhour=8, byminute=27)
            ),
        ]
        for dct, expected in testData:
            output = RecurrenceRule.fromDict(dct)
            self.assertEqual(output, expected,
                '\ninput:    {}\noutput:   {}\nexpected: {}'.format(dct, output, expected)
            )

    def testGetNext(self):
        # rrule after() does not work with dates in the past, so compute a refDate in the future
        year = datetime.now().year + 1
        refDate = datetime(year, 1, 1, 9, 10)

        rule = RecurrenceRule(rrule.DAILY, byhour=10)
        nextDate = rule.getNext(refDate=refDate)
        self.assertEqual(nextDate, refDate.replace(hour=10, minute=0))

        rule = RecurrenceRule(rrule.DAILY, byhour=9)
        nextDate = rule.getNext(refDate=refDate)
        self.assertEqual(nextDate, refDate.replace(day=2, hour=9, minute=0))

        rule = RecurrenceRule(rrule.YEARLY, bymonth=2, bymonthday=23)
        nextDate = rule.getNext(refDate=refDate)
        self.assertEqual(nextDate, refDate.replace(month=2, day=23, hour=0, minute=0))
