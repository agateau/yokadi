# -*- coding: UTF-8 -*-
"""
Mass edit test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import unittest

from yokadi.core import db
from yokadi.core.db import NOTE_KEYWORD
from yokadi.core import dbutils
from yokadi.core.yokadiexception import YokadiException
from yokadi.ycli import massedit
from yokadi.ycli import tui
from yokadi.ycli.massedit import MEditEntry, parseMEditText, ParseError


class MassEditTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        # FIXME: Do this in db
        dbutils.getOrCreateKeyword(NOTE_KEYWORD, interactive=False)
        self.session = db.getSession()
        tui.clearInputAnswers()

    def testApplyMEditChanges(self):
        prj = dbutils.getOrCreateProject("p1", interactive=False)
        t1 = dbutils.addTask("p1", "Change text", {})
        tui.addInputAnswers("y", "y")
        t2 = dbutils.addTask("p1", "Change keywords", {"k1": None, "k2": 1})
        t3 = dbutils.addTask("p1", "Done", {})
        t3.status = "started"
        t4 = dbutils.addTask("p1", "Deleted", {})
        t5 = dbutils.addTask("p1", "Moved", {})
        self.session.commit()
        deletedId = t4.id

        oldList = massedit.createEntriesForProject(prj)
        newList = [
            MEditEntry(None, "new", u"Added", {}),
            MEditEntry(t1.id, "new", u"New text", {}),
            MEditEntry(t2.id, "new", u"Change keywords", {"k2": 2, "k3": None}),
            MEditEntry(t5.id, "new", u"Moved", {}),
            MEditEntry(t3.id, "done", u"Done", {}),
        ]

        massedit.applyChanges(prj, oldList, newList, interactive=False)
        self.session.commit()

        newTask = self.session.query(db.Task).filter_by(title=u"Added").one()

        self.assertEqual(t1.title, u"New text")
        self.assertEqual(t2.getKeywordDict(), {"k2": 2, "k3": None})
        self.assertEqual(t3.status, "done")
        self.assertTrue(t3.doneDate)
        self.assertRaises(YokadiException, dbutils.getTaskFromId, deletedId)
        self.assertEqual(newTask.urgency, 5)
        self.assertEqual(t1.urgency, 4)
        self.assertEqual(t2.urgency, 3)
        self.assertEqual(t5.urgency, 2)
        self.assertEqual(t3.urgency, 1)

    def testApplyMEditChangesUnknownIds(self):
        prj = dbutils.getOrCreateProject("p1", interactive=False)
        t1 = dbutils.addTask("p1", "Foo", {})
        t2 = dbutils.addTask("p1", "Bar", {})

        oldList = massedit.createEntriesForProject(prj)
        newList = [
            MEditEntry(t1.id, "new", t1.title, {}),
            MEditEntry(t2.id + 1, "new", t2.title, {}),
        ]

        self.assertRaises(YokadiException, massedit.applyChanges, prj, oldList,
                          newList, interactive=False)

    def testParseMEditText(self):
        text = """1 N Hello
            4 N Some keywords @foo @bar=1
            6 S A started task
            12 D A done task
            - A newly added task
            - OneWordNewTask

            # A comment
            """
        expected = [
            MEditEntry(1, "new", u"Hello", {}),
            MEditEntry(4, "new", u"Some keywords", {"foo": None, "bar": 1}),
            MEditEntry(6, "started", u"A started task", {}),
            MEditEntry(12, "done", u"A done task", {}),
            MEditEntry(None, "new", u"A newly added task", {}),
            MEditEntry(None, "new", u"OneWordNewTask", {}),
        ]
        output = parseMEditText(text)

        self.assertEqual(output, expected)

    def testParseMEditTextErrors(self):
        testData = [
            # Duplicate id
            """
            1 N X
            1 N Y
            """,
            # Invalid id
            """
            A N X
            """,
            # Invalid status
            """
            1 z Y
            """,
            # Invalid line
            """
            bla
            """
        ]
        for text in testData:
            self.assertRaises(ParseError, parseMEditText, text)

    def testOnlyListTasks(self):
        prj = dbutils.getOrCreateProject("p1", interactive=False)
        dbutils.addTask("p1", "Task", {})
        dbutils.addTask("p1", "Note", {NOTE_KEYWORD: None})

        oldList = massedit.createEntriesForProject(prj)
        self.assertEqual(len(oldList), 1)

    def testCreateMEditText(self):
        e1 = MEditEntry(1, "N", "Hello", {})
        e2 = MEditEntry(2, "S", "Started", {})
        EXPECTED_TEXT = """1 N Hello
2 S Started

# doc1
#
# doc2
"""

        txt = massedit.createMEditText([e1, e2], docComment="doc1\n\ndoc2\n")
        self.assertEqual(txt, EXPECTED_TEXT)
# vi: ts=4 sw=4 et
