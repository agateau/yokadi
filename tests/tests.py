#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Yokadi unit tests

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPLv3
"""

import unittest
from os.path import dirname, join, pardir
import sys
sys.path.append(join(dirname(__file__), pardir))

from parseutilstestcase import ParseUtilsTestCase
from yokadioptionparsertestcase import YokadiOptionParserTestCase
from dateutilstestcase import DateUtilsTestCase
from projecttestcase import ProjectTestCase

if __name__ == "__main__":
    unittest.main()
# vi: ts=4 sw=4 et
