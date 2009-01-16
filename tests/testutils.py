# -*- coding: UTF-8 -*-
"""
Project test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
import os
import unittest

import db

DB_FILENAME = "unittest.db"

class DbTestCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(DB_FILENAME):
            os.unlink(DB_FILENAME)
        db.connectDatabase(DB_FILENAME)
# vi: ts=4 sw=4 et
