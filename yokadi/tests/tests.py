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
from yokadi.core import db

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
from dumptestcase import DumpTestCase
from gitvcsimpltestcase import GitVcsImplTestCase
from pulltestcase import PullTestCase
from textpulluitestcase import TextPullUiTestCase
from keywordfiltertestcase import KeywordFilterTestCase
from recurrenceruletestcase import RecurrenceRuleTestCase
from synccmdtestcase import SyncCmdTestCase
from conflictingobjecttestcase import ConflictingObjectTestCase
from dbreplicatortestcase import DbReplicatorTestCase
from conflictutilstestcase import ConflictUtilsTestCase
from syncmanagertestcase import SyncManagerTestCase


def main():
    unittest.main()

if __name__ == "__main__":
    main()
# vi: ts=4 sw=4 et
