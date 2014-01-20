# -*- coding: UTF-8 -*-
"""
A simple exception class for Yokadi

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""


class YokadiException(Exception):
    """Yokadi Exceptions"""
    pass


class BadUsageException(YokadiException):
    """Exception when user does not pass correct arguments to a command"""
    pass
# vi: ts=4 sw=4 et
