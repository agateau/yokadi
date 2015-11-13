#!/usr/bin/env python3
import os
import unittest

from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.sync import sync
from yokadi.sync.gitvcsimpl import GitVcsImpl


class ImportExportTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

    def testDump(self):
        t1 = dbutils.addTask("prj1", "Foo", keywordDict=dict(kw1=1, kw2=None), interactive=False)
        t2 = dbutils.addTask("prj1", "Bar", keywordDict=dict(kw1=2), interactive=False)
        t3 = dbutils.addTask("prj2", "Baz", interactive=False)

        vcsImpl = GitVcsImpl()
        with TemporaryDirectory() as tmpDir:
            dumpDir = os.path.join(tmpDir, "dump")
            sync.dump(dumpDir, vcsImpl)


    def testSyncOnlyLocalChanges(self):
        pass


    def testSyncOnlyRemoteChanges(self):
        pass


    def testSyncLocalAndRemoteChanges(self):
        pass


    def testSyncConflict(self):
        pass
