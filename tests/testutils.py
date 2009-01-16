# -*- coding: UTF-8 -*-
"""
Utils for unit-test
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
import unittest

import db

def clearDatabase():
    """
    Clear all tables of the database. Should be called in the setUp() method of
    the testcase. Useful to ensure unit-tests start from a blank state.
    """
    for table in db.TABLE_LIST:
        table.clearTable()
# vi: ts=4 sw=4 et
