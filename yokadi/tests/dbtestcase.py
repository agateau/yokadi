"""
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import unittest

from yokadi.core import db


class DbTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()

    def testSetVersion(self):
        newVersion = db.DB_VERSION + 1
        db._database.setVersion(newVersion)
        version = db._database.getVersion()
        self.assertEqual(version, newVersion)
