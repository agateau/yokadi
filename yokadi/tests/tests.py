#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Yokadi unit tests

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

try:
    import icalendar  # noqa: F401
    hasIcalendar = True
except ImportError:
    hasIcalendar = False
    print("icalendar is not installed, some tests won't be run")

from parseutilstestcase import ParseUtilsTestCase  # noqa: F401
from yokadioptionparsertestcase import YokadiOptionParserTestCase  # noqa: F401
from ydateutilstestcase import YDateUtilsTestCase  # noqa: F401
from dbutilstestcase import DbUtilsTestCase  # noqa: F401
from projecttestcase import ProjectTestCase  # noqa: F401
from completerstestcase import CompletersTestCase  # noqa: F401
from tasktestcase import TaskTestCase  # noqa: F401
from bugtestcase import BugTestCase  # noqa: F401
from aliastestcase import AliasTestCase  # noqa: F401
from textlistrenderertestcase import TextListRendererTestCase  # noqa: F401
if hasIcalendar:
    from icaltestcase import IcalTestCase  # noqa: F401
from keywordtestcase import KeywordTestCase  # noqa: F401
from cryptotestcase import CryptoTestCase  # noqa: F401
from tuitestcase import TuiTestCase  # noqa: F401
from helptestcase import HelpTestCase  # noqa: F401
from conftestcase import ConfTestCase  # noqa: F401
from massedittestcase import MassEditTestCase  # noqa: F401
from basepathstestcase import BasePathsUnixTestCase, BasePathsWindowsTestCase  # noqa: F401
from keywordfiltertestcase import KeywordFilterTestCase  # noqa: F401
from recurrenceruletestcase import RecurrenceRuleTestCase  # noqa: F401
from argstestcase import ArgsTestCase  # noqa: F401


def main():
    unittest.main()


if __name__ == "__main__":
    main()
# vi: ts=4 sw=4 et
