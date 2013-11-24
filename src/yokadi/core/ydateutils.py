# -*- coding: UTF-8 -*-
"""
Date utilities.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import time
import operator
from datetime import date, datetime, timedelta

from ycli import parseutils
from core.yokadiexception import YokadiException

WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
SHORT_WEEKDAYS = {"mo": 0, "tu": 1, "we": 2, "th": 3, "fr": 4, "sa": 5, "su": 6}

TIME_HINT_BEGIN = "begin"
TIME_HINT_END = "end"


def guessDateFormat(tDate):
    """Guess a date format.
    @param tDate: date string like 30/08/2008 or 30/08 or 30
    @return: date format as a string like %d/%m/%Y or %d/%m or %d"""
    if tDate.count("/") == 2:
        year = tDate.split("/")[2]
        if len(year) == 4:
            fDate = "%d/%m/%Y"
        elif len(year) == 2:
            fDate = "%d/%m/%y"
    elif tDate.count("/") == 1:
        fDate = "%d/%m"
    else:
        fDate = "%d"
    return fDate


def guessTimeFormat(tTime):
    """Guess a time format.
    @param tTime: time string like 12:30:45 or 12:30 or 12
    @return: time format as a string like %H:%M:%S or %H:%M or %H"""
    if tTime.count(":") == 2:
        fTime = "%H:%M:%S"
    elif tTime.count(":") == 1:
        fTime = "%H:%M"
    else:
        fTime = "%H"
    return fTime


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

    def applyTimeHint(date, hint):
        if not hint:
            return date
        if hint == TIME_HINT_BEGIN:
            return date.replace(hour=0, minute=0, second=0)
        elif hint == TIME_HINT_END:
            return date.replace(hour=23, minute=59, second=59)
        else:
            raise Exception("Unknown hint %s" % hint)

    line = parseutils.simplifySpaces(line)
    if not line:
        raise YokadiException("Date is empty")

    # Date & Time format
    fDate = None
    fTime = None

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
    firstWord = line.split()[0].lower()

    weekdayDict = {"tomorrow": (today.weekday() + 1) % 7}
    weekdayDict.update(WEEKDAYS)
    weekdayDict.update(SHORT_WEEKDAYS)
    weekday = weekdayDict.get(firstWord)
    if weekday is not None:
        date = today + timedelta(days=(weekday - today.weekday()) % 7)
        if " " in line:
            timeText = line.split()[1]
            fTime = guessTimeFormat(timeText)
            try:
                tTime = datetime(*time.strptime(timeText, fTime)[0:5]).time()
            except ValueError, e:
                raise YokadiException("Invalid time format: %s" % e)
            date = datetime.combine(date, tTime)
        else:
            date = applyTimeHint(date, hint)
        return date

    # Absolute date and/or time
    date = None
    if " " in line:
        # We assume user give date & time
        tDate, tTime = line.split(' ', 1)
        fDate = guessDateFormat(tDate)
        fTime = guessTimeFormat(tTime)
        try:
            date = datetime(*time.strptime(line, "%s %s" % (fDate, fTime))[0:5])
        except Exception, e:
            raise YokadiException("Unable to understand date & time format: %s" % e)
    else:
        if ":" in line:
            fTime = guessTimeFormat(line)
            try:
                tTime = datetime(*time.strptime(line, fTime)[0:5]).time()
            except ValueError, e:
                raise YokadiException("Invalid time format: %s" % e)
            date = datetime.combine(today, tTime)
        else:
            fDate = guessDateFormat(line)
            try:
                date = datetime(*time.strptime(line, fDate)[0:5])
            except ValueError, e:
                raise YokadiException("Invalid date format: %s" % e)
            date = applyTimeHint(date, hint)
    assert date

    if fDate:
        # Set year and/or month to current date if not given
        if not "%Y" in fDate:
            date = date.replace(year=today.year)
        if not "%m" in fDate:
            date = date.replace(month=today.month)
    return date


def formatTimeDelta(delta):
    """Friendly format a time delta:
        - Show only days if delta > 1 day
        - Show only hours and minutes othewise
    @param timeLeft: Remaining time
    @type timeLeft: timedelta (from datetime)
    @return: formated  str"""
    prefix = ""
    if delta < timedelta(0):
        delta = -delta
        prefix = "-"

    if delta.days > 7:
        value = "%dw" % (delta.days / 7)
        days = delta.days % 7
        if days > 0:
            value = value + ", %dd" % days
    elif delta.days > 0:
        value = "%dd" % delta.days
    else:
        minutes = delta.seconds / 60
        hours = minutes / 60
        minutes = minutes % 60
        if hours > 0:
            value = "%dh " % hours
        else:
            value = ""
        value = value + "%dm" % minutes

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
    if len(day) == 2 and SHORT_WEEKDAYS.has_key(day):
        dayNumber = SHORT_WEEKDAYS[day]
    elif WEEKDAYS.has_key(day):
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

# vi: ts=4 sw=4 et
