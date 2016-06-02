# -*- coding: UTF-8 -*-
"""
Date utilities.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import operator
from datetime import date, datetime, timedelta

from dateutil import rrule

from yokadi.ycli import basicparseutils
from yokadi.core.yokadiexception import YokadiException

WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
SHORT_WEEKDAYS = {"mo": 0, "tu": 1, "we": 2, "th": 3, "fr": 4, "sa": 5, "su": 6}
FREQUENCIES = {0: "Yearly", 1: "Monthly", 2: "Weekly", 3: "Daily"}

TIME_HINT_BEGIN = "begin"
TIME_HINT_END = "end"

DATE_FORMATS = [
    "%d/%m/%Y",
    "%d/%m/%y",
    "%d/%m",
    ]

TIME_FORMATS = [
    "%H:%M:%S",
    "%H:%M",
    "%H",
    ]


def parseDateTimeDelta(line):
    # FIXME: Do we really want to support float deltas?
    try:
        delta = float(line[:-1])
    except ValueError:
        raise YokadiException("Timeshift must be a float or an integer")

    suffix = line[-1].upper()
    if   suffix == "W":
        return timedelta(days=delta * 7)
    elif suffix == "D":
        return timedelta(days=delta)
    elif suffix == "H":
        return timedelta(hours=delta)
    elif suffix == "M":
        return timedelta(minutes=delta)
    else:
        raise YokadiException("Unable to understand time shift. See help t_set_due")


def testFormats(text, formats):
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt), fmt
        except ValueError:
            pass
    return None, None


def guessTime(text):
    afternoon = False
    # We do not use the "%p" format to handle AM/PM because its behavior is
    # locale-dependent
    if text[-1] == "m":
        suffix = text[-2:]
        if suffix == "am":
            pass
        elif suffix == "pm":
            afternoon = True
        else:
            raise ValueError
        text = text[:-2].strip()

    out, fmt = testFormats(text, TIME_FORMATS)
    if out is None:
        return None
    if afternoon:
        out += timedelta(hours=12)
    return out.time()


def parseHumaneDateTime(line, hint=None, today=None):
    """Parse human date and time and return structured datetime object
    Datetime  can be absolute (23/10/2008 10:38) or relative (+5M, +3H, +1D, +6W)
    @param line: human date / time
    @param hint: optional hint to tell whether time should be set to the
    beginning or the end of the day when not specified.
    @param today: optional parameter to define a fake today date. Useful for
    unit testing.
    @type line: str
    @return: datetime object"""
    def guessDate(text):
        out, fmt = testFormats(text, DATE_FORMATS)
        if not out:
            return None
        if not "%y" in fmt and not "%Y" in fmt:
            out = out.replace(year=today.year)
        return out.date()

    def applyTimeHint(date, hint):
        if not hint:
            return date
        if hint == TIME_HINT_BEGIN:
            return date.replace(hour=0, minute=0, second=0)
        elif hint == TIME_HINT_END:
            return date.replace(hour=23, minute=59, second=59)
        else:
            raise Exception("Unknown hint %s" % hint)

    line = basicparseutils.simplifySpaces(line).lower()
    if not line:
        raise YokadiException("Date is empty")

    if today is None:
        today = datetime.today().replace(microsecond=0)

    if line == "now":
        return today

    if line == "today":
        return applyTimeHint(today, hint)

    # Check for "+<delta>" format
    if line.startswith("+"):
        return today + parseDateTimeDelta(line[1:])
    if line.startswith("-"):
        return today - parseDateTimeDelta(line[1:])

    # Check for "<weekday> [<time>]" format
    firstWord = line.split()[0]

    weekdayDict = {
        "today": today.weekday(),
        "tomorrow": (today.weekday() + 1) % 7,
        }
    weekdayDict.update(WEEKDAYS)
    weekdayDict.update(SHORT_WEEKDAYS)
    weekday = weekdayDict.get(firstWord)
    if weekday is not None:
        date = today + timedelta(days=(weekday - today.weekday()) % 7)
        if " " in line:
            timeText = line.split(' ', 1)[1]
            tTime = guessTime(timeText)
            if tTime is None:
                raise YokadiException("Unable to understand time '%s'" % timeText)
            date = datetime.combine(date, tTime)
        else:
            date = applyTimeHint(date, hint)
        return date

    if " " in line:
        # Absolute date and time?
        dateText, timeText = line.split(' ', 1)
        tDate = guessDate(dateText)
        if tDate is not None:
            tTime = guessTime(timeText)
            if tTime is not None:
                return datetime.combine(tDate, tTime)

    # Only date?
    tDate = guessDate(line)
    if tDate is not None:
        dt = datetime.combine(tDate, today.time())
        return applyTimeHint(dt, hint)

    # Only time?
    tTime = guessTime(line)
    if tTime is not None:
        tDate = datetime.combine(today.date(), tTime)
        if tTime > today.time():
            return tDate
        else:
            return tDate + timedelta(days=1)

    raise YokadiException("Unable to understand date '%s'" % line)


def formatTimeDelta(delta):
    """Friendly format a time delta:
        - Show only days if delta > 1 day
        - Show only hours and minutes otherwise
    @param timeLeft: Remaining time
    @type timeLeft: timedelta (from datetime)
    @return: formated  str"""
    prefix = ""
    value = ""
    if delta < timedelta(0):
        delta = -delta
        prefix = "-"

    if delta.days >= 365:
        value = "%dY" % (delta.days / 365)
        days = delta.days % 365
        if days > 30:
            value += ", %dM" % (days / 30)
    elif delta.days > 50:
        value = "%dM" % (delta.days / 30)
        days = delta.days % 30
        if days > 0:
            value += ", %dd" % days
    elif delta.days >= 7:
        value = "%dw" % (delta.days / 7)
        days = delta.days % 7
        if days > 0:
            value += ", %dd" % days
    elif delta.days > 0:
        value = "%dd" % delta.days
    else:
        minutes = delta.seconds / 60
        hours = minutes / 60
        minutes = minutes % 60
        if hours >= 1:
            value = "%dh " % hours
        else:
            value = ""
        value += "%dm" % minutes

    return prefix + value


def getHourAndMinute(token):
    """Extract hour and minute from HH:MM token
    #TODO: move this in date utils
    @param token: HH:MM string
    @return: (int, int)"""
    try:
        hour, minute = token.split(":")
    except ValueError:
        hour = token
        minute = 0
    try:
        hour = int(hour)
        minute = int(minute)
    except ValueError:
        raise YokadiException("You must provide integer for hour/minute")
    return hour, minute


def getWeekDayNumberFromDay(day):
    """Return week day number (0-6) from week day name (short or long)
    @param day: week day as a string in short or long format (in english)
    @type day: str
    @return: week day number (int)"""
    if len(day) == 2 and day in SHORT_WEEKDAYS:
        dayNumber = SHORT_WEEKDAYS[day]
    elif day in WEEKDAYS:
        dayNumber = WEEKDAYS[day]
    else:
        raise YokadiException("Day must be one of the following: [mo]nday, [tu]esday, [we]nesday, [th]ursday, [fr]iday, [sa]turday, [su]nday")
    return dayNumber


def parseDateLimit(line, today=None):
    """Parse a string of the form <operator><limit>
    - operator is one of: < <= >= > (default to <=)
    - limit is a date as understood by parseHumaneDateTime()

    @param line: the string to parse
    @param today: optional specification of current day, for unit testing
    @return: (operator, date)"""

    # Order matters: match longest operators first!
    operators = [
        ("<=", operator.__le__, TIME_HINT_END),
        (">=", operator.__ge__, TIME_HINT_BEGIN),
        (">", operator.__gt__, TIME_HINT_END),
        ("<", operator.__lt__, TIME_HINT_BEGIN),
        ]

    op = operator.__le__
    hint = TIME_HINT_END
    for txt, loopOp, loopHint in operators:
        if line.startswith(txt):
            op = loopOp
            hint = loopHint
            line = line[len(txt):]
            break

    limit = parseHumaneDateTime(line, today=today, hint=hint)
    return op, limit


def parseMinDate(line):
    # Parse the line string and return a minimum date
    minDate = date.today()
    if line == "today":
        pass
    elif line == "thisweek":
        minDate -= timedelta(minDate.weekday())
    elif line == "thismonth":
        minDate = minDate.replace(day=1)
    else:
        minDate = parseHumaneDateTime(line).date()

    return minDate


class RecurrenceRule(object):
    """Thin wrapper around dateutil.rrule
    which brings:
    - Serialization to/from dict
    - Parsing methods
    - Sane defaults (byhour = byminute = bysecond = 0)
    - __eq__ operator
    - Readable name
    """
    def __init__(self, frequency=None, **kwargs):
        if frequency is None:
            self._rr = None
            return
        args = dict(byhour=0, byminute=0, bysecond=0)
        args.update(kwargs)
        self._rr = rrule.rrule(frequency, **args)

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
                bymonth = [1, 4, 7, 10]
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
        if self._rr is None:
            return {}

        return dict(
                freq=self._rr._freq,
                bymonth=self._rr._bymonth,
                bymonthday=self._rr._bymonthday,
                byweekday=self._rr._byweekday,
                byhour=self._rr._byhour,
                byminute=self._rr._byminute
            )

    def getNext(self, refDate=None):
        """Return next date of recurrence after given date
        @param refDate: reference date used to compute the next occurence of recurrence
        @type refDate: datetime
        @return: next occurence (datetime)"""
        if self._rr is None:
            return None
        if refDate is None:
            refDate = datetime.now().replace(second=0, microsecond=0)
        return self._rr.after(refDate)

    def getFrequencyAsString(self):
        """Return a string for the frequency"""
        if self._rr is None:
            return ""
        return FREQUENCIES[self._rr._freq]

    def __eq__(self, other):
        return self.toDict() == other.toDict()

    def __bool__(self):
        return bool(self.toDict())

    def __repr__(self):
        return repr(self.toDict())

# vi: ts=4 sw=4 et
