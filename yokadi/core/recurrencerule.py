"""
Date utilities.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from datetime import datetime

from dateutil import rrule

from yokadi.core.ydateutils import getHourAndMinute, getWeekDayNumberFromDay, parseHumaneDateTime
from yokadi.core.yokadiexception import YokadiException


FREQUENCIES = {0: "Yearly", 1: "Monthly", 2: "Weekly", 3: "Daily"}

ALL_DAYS = (rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR, rrule.SA, rrule.SU)


class RecurrenceRule(object):
    """Thin wrapper around dateutil.rrule which brings:

    - Serialization to/from dict
    - Parsing methods
    - Sane defaults (byhour = byminute = bysecond = 0)
    - __eq__ operator
    - Readable name

    Dict format:
        freq: 0..3, see FREQUENCIES dict
        bymonth: tuple<1..12>
        bymonthday: tuple<1..31>
        byweekday: tuple<0..6> or {pos: -1;1..4, weekday: 0..6}
        byhour: tuple<0..23>
        byminute: tuple<0..59>

    Constructor arguments: same as dict format except tuples can be int or None
    for convenience
    """
    def __init__(self, freq=None, bymonth=None, bymonthday=None, byweekday=None, byhour=0, byminute=0):
        def tuplify(value):
            if value is None:
                return ()
            if isinstance(value, int):
                return (value,)
            else:
                return tuple(value)

        self._freq = freq
        self._bymonth = tuplify(bymonth)
        self._bymonthday = tuplify(bymonthday)
        if isinstance(byweekday, dict):
            self._byweekday = byweekday
        else:
            self._byweekday = tuplify(byweekday)
        self._byhour = tuplify(byhour)
        self._byminute = tuplify(byminute)

    @staticmethod
    def fromDict(dct):
        if not dct:
            return RecurrenceRule()
        return RecurrenceRule(**dct)

    @staticmethod
    def fromHumaneString(line):
        """Take a string following t_recurs format, returns a RecurrenceRule instance or None
        """
        freq = byminute = byhour = byweekday = bymonthday = bymonth = None

        tokens = line.split()

        tokens[0] = tokens[0].lower()

        if tokens[0] == "none":
            return RecurrenceRule()

        if tokens[0] == "daily":
            if len(tokens) != 2:
                raise YokadiException("You should give time for daily task")
            freq = rrule.DAILY
            byhour, byminute = getHourAndMinute(tokens[1])
        elif tokens[0] == "weekly":
            freq = rrule.WEEKLY
            if len(tokens) != 3:
                raise YokadiException("You should give day and time for weekly task")
            byweekday = getWeekDayNumberFromDay(tokens[1].lower())
            byhour, byminute = getHourAndMinute(tokens[2])
        elif tokens[0] in ("monthly", "quarterly"):
            if tokens[0] == "monthly":
                freq = rrule.MONTHLY
            else:
                # quarterly
                freq = rrule.YEARLY
                bymonth = (1, 4, 7, 10)
            if len(tokens) < 3:
                raise YokadiException("You should give day and time for %s task" % (tokens[0],))
            try:
                bymonthday = int(tokens[1])
                byhour, byminute = getHourAndMinute(tokens[2])
            except ValueError:
                POSITION = {"first": 1, "second": 2, "third": 3, "fourth": 4, "last": -1}
                if tokens[1].lower() in POSITION and len(tokens) == 4:
                    byweekday = RecurrenceRule.createWeekDay(
                        weekday=getWeekDayNumberFromDay(tokens[2].lower()),
                        pos=POSITION[tokens[1]])
                    byhour, byminute = getHourAndMinute(tokens[3])
                    bymonthday = None  # Default to current day number - need to be blanked
                else:
                    raise YokadiException("Unable to understand date. See help t_recurs for details")
        elif tokens[0] == "yearly":
            freq = rrule.YEARLY
            rDate = parseHumaneDateTime(" ".join(tokens[1:]))
            bymonth = rDate.month
            bymonthday = rDate.day
            byhour = rDate.hour
            byminute = rDate.minute
        else:
            raise YokadiException("Unknown frequency. Available: daily, weekly, monthly and yearly")

        return RecurrenceRule(
            freq,
            bymonth=bymonth,
            bymonthday=bymonthday,
            byweekday=byweekday,
            byhour=byhour,
            byminute=byminute,
        )

    def toDict(self):
        if not self:
            return {}

        return dict(
            freq=self._freq,
            bymonth=self._bymonth,
            bymonthday=self._bymonthday,
            byweekday=self._byweekday,
            byhour=self._byhour,
            byminute=self._byminute
        )

    def _rrule(self):
        if isinstance(self._byweekday, dict):
            day = ALL_DAYS[self._byweekday["weekday"]]
            byweekday = day(self._byweekday["pos"])
        else:
            byweekday = self._byweekday

        return rrule.rrule(
            freq=self._freq,
            bymonth=self._bymonth,
            bymonthday=self._bymonthday,
            byweekday=byweekday,
            byhour=self._byhour,
            byminute=self._byminute,
            bysecond=0
        )

    def getNext(self, refDate=None):
        """Return next date of recurrence after given date
        @param refDate: reference date used to compute the next occurence of recurrence
        @type refDate: datetime
        @return: next occurence (datetime)"""
        if not self:
            return None
        if refDate is None:
            refDate = datetime.now()
        refDate.replace(second=0, microsecond=0)
        return self._rrule().after(refDate)

    def getFrequencyAsString(self):
        """Return a string for the frequency"""
        if not self:
            return ""
        return FREQUENCIES[self._freq]

    @staticmethod
    def createWeekDay(pos, weekday):
        return dict(pos=pos, weekday=weekday)

    def __eq__(self, other):
        return self.toDict() == other.toDict()

    def __bool__(self):
        return self._freq is not None

    def __repr__(self):
        return repr(self.toDict())

# vi: ts=4 sw=4 et
