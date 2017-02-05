#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Yokadi unit tests

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import cProfile
import os
import pstats
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

try:
    import icalendar
    hasIcalendar = True
except ImportError:
    hasIcalendar = False
    print("icalendar is not installed, some tests won't be run")

from parseutilstestcase import ParseUtilsTestCase
from yokadioptionparsertestcase import YokadiOptionParserTestCase
from ydateutilstestcase import YDateUtilsTestCase
from dbutilstestcase import DbUtilsTestCase
from projecttestcase import ProjectTestCase
from completerstestcase import CompletersTestCase
from tasktestcase import TaskTestCase
from bugtestcase import BugTestCase
from aliastestcase import AliasTestCase
from textlistrenderertestcase import TextListRendererTestCase
if hasIcalendar:
    from icaltestcase import IcalTestCase
from keywordtestcase import KeywordTestCase
from cryptotestcase import CryptoTestCase
from tuitestcase import TuiTestCase
from helptestcase import HelpTestCase
from conftestcase import ConfTestCase
from massedittestcase import MassEditTestCase
from basepathstestcase import BasePathsUnixTestCase, BasePathsWindowsTestCase
from keywordfiltertestcase import KeywordFilterTestCase
from recurrenceruletestcase import RecurrenceRuleTestCase


def profileMain(profileFileName):
    pr = cProfile.Profile()
    pr.enable()
    unittest.main(exit=False)
    pr.disable()

    with open(profileFileName, "w") as fp:
        sortby = "cumulative"
        ps = pstats.Stats(pr, stream=fp).sort_stats(sortby)
        ps.print_stats()


if __name__ == "__main__":
    profileFileName = os.environ.get("YOKADI_PROFILE")
    if profileFileName:
        profileMain(profileFileName)
    else:
        unittest.main()
# vi: ts=4 sw=4 et
