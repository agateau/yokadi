#!/usr/bin/env python3
import os
import unittest

from tempfile import TemporaryDirectory

import icalendar

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.sync.dump import dump
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.yical import icalutils


def getTaskPath(dumpDir, task):
    return os.path.join(dumpDir, "projects", task.project.name, task.uuid + ".ics")


def loadVTodoFromPath(taskFilePath):
    with open(taskFilePath) as fp:
        calData = fp.read()
        cal = icalendar.Calendar.from_ical(calData)
        return cal.walk()[1]


class DumpTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

    def testDump(self):
        t1 = dbutils.addTask("prj1", "Foo", keywordDict=dict(kw1=1, kw2=None), interactive=False)
        t2 = dbutils.addTask("prj1", "Bar", keywordDict=dict(kw1=2), interactive=False)
        t3 = dbutils.addTask("prj2", "Baz", interactive=False)
        t3.description = "Hello"

        vcsImpl = GitVcsImpl()
        with TemporaryDirectory() as tmpDir:
            dumpDir = os.path.join(tmpDir, "dump")
            dump(dumpDir, vcsImpl)

            for task in t1, t2, t3:
                taskFilePath = getTaskPath(dumpDir, task)
                self.assertTrue(os.path.exists(taskFilePath))
                vtodo = loadVTodoFromPath(taskFilePath)
                title = icalutils.icalSummaryToYokadiTaskTitle(vtodo["summary"], task.id)
                self.assertEqual(task.title, title)
                if task.description:
                    self.assertEqual(task.description, vtodo["description"])

    def testUpdateDump(self):
        t1 = dbutils.addTask("prj1", "Foo", keywordDict=dict(kw1=1, kw2=None), interactive=False)
        t2 = dbutils.addTask("prj1", "Bar", keywordDict=dict(kw1=2), interactive=False)
        t3 = dbutils.addTask("prj2", "Baz", interactive=False)

        vcsImpl = GitVcsImpl()
        with TemporaryDirectory() as tmpDir:
            dumpDir = os.path.join(tmpDir, "dump")
            dump(dumpDir, vcsImpl)

            # Do some changes: update t3, add t4, remove t2, then dump again
            newTitle = "New T3 title"
            t3.title = newTitle
            self.session.add(t3)

            t4 = dbutils.addTask("prj2", "New task", interactive=False)
            self.session.add(t4)

            self.session.delete(t2)

            self.session.commit()

            dump(dumpDir, vcsImpl)

            # Check t3 has been updated
            taskFilePath = getTaskPath(dumpDir, t3)
            vtodo = loadVTodoFromPath(taskFilePath)
            title = icalutils.icalSummaryToYokadiTaskTitle(vtodo["summary"], t3.id)
            self.assertEqual(title, newTitle)

            # Check t4 has been dumped
            taskFilePath = getTaskPath(dumpDir, t4)
            self.assertTrue(os.path.exists(taskFilePath))

            # Check t2 file has been removed
            taskFilePath = getTaskPath(dumpDir, t2)
            self.assertFalse(os.path.exists(taskFilePath))
