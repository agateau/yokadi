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


class RecurrenceRule(object):
    """Thin wrapper around dateutil.rrule
    which brings:
    - Serialization to/from dict
    - Parsing methods
    - Sane defaults (byhour = byminute = bysecond = 0)
    - __eq__ operator
    - Readable name
    """
    def __init__(self, freq=None, bymonth=None, bymonthday=None, byweekday=None, byhour=0, byminute=0):
        self._freq = freq
        self._bymonth = bymonth
        self._bymonthday = bymonthday
        self._byweekday = byweekday
        self._byhour = byhour
        self._byminute = byminute

    @staticmethod
    def fromDict(dct):
        if not dct:
            return RecurrenceRule()

        return RecurrenceRule(dct["freq"],
                bymonth=dct["bymonth"],
                bymonthday=dct["bymonthday"],
                byweekday=dct["byweekday"],
                byhour=dct["byhour"],
                byminute=dct["byminute"])

    @staticmethod
    def fromHumaneString(line):
        """Take a string following t_recurs format, returns a Rrule instance or None
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
                POSITION = {"first": 1, "second": 2, "third": 3, "fourth": 4, "last":-1}
                if tokens[1].lower() in POSITION and len(tokens) == 4:
                    byweekday = rrule.weekday(getWeekDayNumberFromDay(tokens[2].lower()),
                                              POSITION[tokens[1]])
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

        return RecurrenceRule(freq,
                bymonth=bymonth,
                bymonthday=bymonthday,
                byweekday=byweekday,
                byhour=byhour,
                byminute=byminute,
                )

    def toDict(self):
        if not self._freq:
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
        return rrule.rrule(freq=self._freq,
                bymonth=self._bymonth,
                bymonthday=self._bymonthday,
                byweekday=self._byweekday,
                byhour=self._byhour,
                byminute=self._byminute,
                bysecond=0
                )

    def getNext(self, refDate=None):
        """Return next date of recurrence after given date
        @param refDate: reference date used to compute the next occurence of recurrence
        @type refDate: datetime
        @return: next occurence (datetime)"""
        if not self._freq:
            return None
        if refDate is None:
            refDate = datetime.now()
        refDate.replace(second=0, microsecond=0)
        return self._rrule().after(refDate)

    def getFrequencyAsString(self):
        """Return a string for the frequency"""
        if not self._freq:
            return ""
        return FREQUENCIES[self._freq]

    def __eq__(self, other):
        return self.toDict() == other.toDict()

    def __bool__(self):
        return bool(self._freq)

    def __repr__(self):
        return repr(self.toDict())

# vi: ts=4 sw=4 et
