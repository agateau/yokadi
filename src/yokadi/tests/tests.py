#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Yokadi unit tests

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import db

from parseutilstestcase import ParseUtilsTestCase
from yokadioptionparsertestcase import YokadiOptionParserTestCase
from dateutilstestcase import DateUtilsTestCase
from dbutilstestcase import DbUtilsTestCase
from projecttestcase import ProjectTestCase
from completerstestcase import CompletersTestCase
from tasktestcase import TaskTestCase
from bugtestcase import BugTestCase
from aliastestcase import AliasTestCase
from textlistrenderertestcase import TextListRendererTestCase

DB_FILENAME = "unittest.db"

def main():
    if os.path.exists(DB_FILENAME):
        os.unlink(DB_FILENAME)
    db.connectDatabase(DB_FILENAME)

    unittest.main()

if __name__ == "__main__":
    main()
# vi: ts=4 sw=4 et
