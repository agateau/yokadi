#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Yokadi unit tests

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import unittest

from parseutilstestcase import ParseUtilsTestCase

def main():
    testCases = [ParseUtilsTestCase]
    suites = [unittest.TestLoader().loadTestsFromTestCase(x) for x in testCases]
    suite = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == "__main__":
    main()
# vi: ts=4 sw=4 et
