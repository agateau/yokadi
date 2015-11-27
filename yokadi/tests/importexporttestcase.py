#!/usr/bin/env python3
import os
import unittest

from tempfile import TemporaryDirectory

import icalendar

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.sync import sync
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.yical import icalutils


class ImportExportTestCase(unittest.TestCase):
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
            sync.dump(dumpDir, vcsImpl)

            for task in t1, t2, t3:
                taskFilePath = os.path.join(dumpDir, "projects", task.project.name, task.uuid + ".ics")
                self.assertTrue(os.path.exists(taskFilePath))
                with open(taskFilePath) as fp:
                    calData = fp.read()

                cal = icalendar.Calendar.from_ical(calData)
                vtodo = cal.walk()[1]
                title = icalutils.icalSummaryToYokadiTaskTitle(vtodo["summary"], task.id)
                self.assertEqual(task.title, title)
                if task.description:
                    self.assertEqual(task.description, vtodo["description"])


    def testSyncOnlyLocalChanges(self):
        pass


    def testSyncOnlyRemoteChanges(self):
        pass


    def testSyncLocalAndRemoteChanges(self):
        pass


    def testSyncConflict(self):
        pass
