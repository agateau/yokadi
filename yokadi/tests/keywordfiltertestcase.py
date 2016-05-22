# -*- coding: UTF-8 -*-
"""
Keyword filter test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import unittest

from yokadi.core import db, dbutils
from yokadi.core.dbutils import KeywordFilter


class KeywordFilterTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()

    def testSimpleFilter(self):
        t1 = dbutils.addTask("p1", "t1", interactive=False)
        t2 = dbutils.addTask("p1", "t2", keywordDict={"k1": None}, interactive=False)
        t3 = dbutils.addTask("p1", "t3", keywordDict={"k2": None}, interactive=False)
        t4 = dbutils.addTask("p1", "t4", keywordDict={"k1": None, "k2": None}, interactive=False)

        testData = [
            (KeywordFilter("k1"), {t2, t4}),
            (KeywordFilter("k%"), {t2, t3, t4}),
            (KeywordFilter("k1", negative=True), {t1, t3}),
            (KeywordFilter("k%", negative=True), {t1}),
        ]

        for flt, expected in testData:
            query = self.session.query(db.Task)
            query = flt.apply(query)
            resultSet = {x.title for x in query}
            expectedSet = {x.title for x in expected}
            self.assertEqual(resultSet, expectedSet)
