# coding:utf-8
"""
Ical utils functions
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import icalendar


def convertIcalType(attr):
    """Convert data from icalendar types (vDates, vInt etc.) to python standard equivalent
    @param attr: icalendar type
    @return: python type"""
    if isinstance(attr, (icalendar.vDate, icalendar.vDatetime,
                         icalendar.vDuration, icalendar.vDDDTypes)):
        return attr.dt
    elif isinstance(attr, (icalendar.vInt, icalendar.vFloat)):
        return int(attr)
    else:
        # Default to unicode string
        return str(attr)


def icalPriorityToYokadiUrgency(priority):
    """Convert ical priority (1 / 9) to yokadi urgency (100 / -99)
    @param priority: ical priority
    @return: yokadi urgency"""
    urgency = 100 - 20 * priority
    if urgency > 100: urgency = 100
    if urgency < -99: urgency = -99
    return urgency


def yokadiUrgencyToIcalPriority(urgency):
    """Convert yokadi urgency (100 / -99) to ical priority (1 / 9)
    @param urgency: yokadi urgency
    @return: ical priority"""
    priority = int(-(urgency - 100) / 20)
    if priority > 9: priority = 9
    if priority < 1: priority = 1
    return priority

# vi: ts=4 sw=4 et
