# -*- coding: UTF-8 -*-
"""
Date utilities.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""
import time
from datetime import datetime, timedelta

import colors as C
from yokadiexception import YokadiException


def guessDateFormat(tDate):
    """Guess a date format.
    @param tDate: date string like 30/08/2008 or 30/08 or 30
    @return: date format as a string like %d/%m/%Y or %d/%m or %d"""
    if tDate.count("/")==2:
        fDate="%d/%m/%Y"
    elif tDate.count("/")==1:
        fDate="%d/%m"
    else:
        fDate="%d"
    return fDate


def guessTimeFormat(tTime):
    """Guess a time format.
    @param tTime: time string like 12:30:45 or 12:30 or 12
    @return: time format as a string like %H:%M:%S or %H:%M or %H"""
    if tTime.count(":")==2:
        fTime="%H:%M:%S"
    elif tTime.count(":")==1:
        fTime="%H:%M"
    else:
        fTime="%H"
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


def parseHumaneDateTime(line):
    """Parse human date and time and return structured datetime object
    Datetime  can be absolute (23/10/2008 10:38) or relative (+5M, +3H, +1D, +6W)
    @param line: human date / time
    @type line: str
    @return: datetime object"""

    # Date & Time format
    fDate=None
    fTime=None

    today=datetime.today().replace(microsecond=0)

    if line.startswith("+"):
        date = today + parseDateTimeDelta(line[1:])
    else:
        date = today
        #Absolute date and/or time
        if " " in line:
            # We assume user give date & time
            tDate, tTime=line.split()
            fDate=guessDateFormat(tDate)
            fTime=guessTimeFormat(tTime)
            try:
                date=datetime(*time.strptime(line, "%s %s" % (fDate, fTime))[0:5])
            except Exception, e:
                raise YokadiException("Unable to understand date & time format:\t%s" % e)
        else:
            if ":" in line:
                fTime=guessTimeFormat(line)
                try:
                    tTime=datetime(*time.strptime(line, fTime)[0:5]).time()
                except ValueError, e:
                    raise YokadiException("Invalid date format: %s" % e)
                date=datetime.combine(today, tTime)
            else:
                fDate=guessDateFormat(line)
                try:
                    date=datetime(*time.strptime(line, fDate)[0:5])
                except ValueError, e:
                    raise YokadiException("Invalid date format: %s" % e)
        if fDate:
            # Set year and/or month to current date if not given
            try:
                if not "%Y" in fDate:
                    date=date.replace(year=today.year)
                if not "%m" in fDate:
                    date=date.replace(month=today.month)
            except ValueError, e:
                    raise YokadiException("Invalid date format: %s" % e)
    return date


def formatTimeDelta(timeLeft):
    """Friendly format a time delta :
        - Use fake negative timedelta if needed not to confuse user.
        - Hide seconds when delta > 1 day
        - Hide hours and minutes when delta > 3 days
    @param timeLeft: Remaining time
    @type timeLeft: timedelta (from datetime)
    @return: formated  str"""
    if timeLeft < timedelta(0):
        # Negative timedelta are very confusing, so we manually put a "-" and show a positive timedelta
        timeLeft=-timeLeft
        # Shorten timedelta:
        if timeLeft < timedelta(3):
            formatedTimeLeft=shortenTimeDelta(timeLeft, "datetime")
        else:
            formatedTimeLeft=shortenTimeDelta(timeLeft, "date")
        formatedTimeLeft="-"+formatedTimeLeft
    elif timeLeft < timedelta(1):
        formatedTimeLeft=str(timeLeft)
    elif timeLeft < timedelta(3):
        formatedTimeLeft=shortenTimeDelta(timeLeft, "datetime")
    else:
        formatedTimeLeft=shortenTimeDelta(timeLeft, "date")
    return formatedTimeLeft


def shortenTimeDelta(timeLeft, format):
    """Shorten timeDelta according the format parameter
    @param timeLeft: timedelta to be shorten
    @type timeLeft: timedelta (from datetime)
    @param format: can be "date" (hours, minute and seconds removed) or "datetime" (seconds removed)
    @return: shorten timedelta"""
    if   format=="date":
        return str(timeLeft).split(",")[0]
    elif format=="datetime":
        # Hide seconds (remove the 3 last characters)
        return str(timeLeft)[:-3]
# vi: ts=4 sw=4 et
