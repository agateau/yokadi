# -*- coding: UTF-8 -*-
"""
Task related commands.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""
from time import strptime
from datetime import datetime, timedelta

from utils import guessDateFormat, guessTimeFormat
from yokadiexception import YokadiException

def parseHumaneDateTime(line):
    # Date & Time format
    fDate=None
    fTime=None

    today=datetime.today().replace(microsecond=0)

    # Initialise dueDate to now (may be now + fixe delta ?)
    dueDate=today # Safe because datetime objects are immutables

    if line.startswith("+"):
        #Delta/relative date and/or time
        line=line.upper().strip("+")
        try:
            if   line.endswith("W"):
                dueDate=today+timedelta(days=float(line[0:-1])*7)
            elif line.endswith("D"):
                dueDate=today+timedelta(days=float(line[0:-1]))
            elif line.endswith("H"):
                dueDate=today+timedelta(hours=float(line[0:-1]))
            elif line.endswith("M"):
                dueDate=today+timedelta(minutes=float(line[0:-1]))
            else:
                raise YokadiException("Unable to understand time shift. See help t_set_due")
        except ValueError:
            raise YokadiException("Timeshift must be a float or an integer")
    else:
        #Absolute date and/or time
        if " " in line:
            # We assume user give date & time
            tDate, tTime=line.split()
            fDate=guessDateFormat(tDate)
            fTime=guessTimeFormat(tTime)
            try:
                dueDate=datetime(*strptime(line, "%s %s" % (fDate, fTime))[0:5])
            except Exception, e:
                raise YokadiException("Unable to understand date & time format:\t%s" % e)
        else:
            if ":" in line:
                fTime=guessTimeFormat(line)
                try:
                    tTime=datetime(*strptime(line, fTime)[0:5]).time()
                except ValueError:
                    raise YokadiException("Invalid time format")
                dueDate=datetime.combine(today, tTime)
            else:
                fDate=guessDateFormat(line)
                try:
                    dueDate=datetime(*strptime(line, fDate)[0:5])
                except ValueError:
                    raise YokadiException("Invalid date format")
        if fDate:
            # Set year and/or month to current date if not given
            if not "%Y" in fDate:
                dueDate=dueDate.replace(year=today.year)
            if not "%M" in fDate:
                dueDate=dueDate.replace(month=today.month)

    return dueDate

# vi: ts=4 sw=4 et
