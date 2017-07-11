# -*- coding: UTF-8 -*-
"""
Standard codes for shell colors.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""

import sys

if sys.stdout.isatty():
    BOLD = '\033[01m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    ORANGE = '\033[33m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    GREY = '\033[37m'
    RESET = '\033[0;0m'
else:
    BOLD = ''
    RED = ''
    GREEN = ''
    ORANGE = ''
    PURPLE = ''
    CYAN = ''
    GREY = ''
    RESET = ''
