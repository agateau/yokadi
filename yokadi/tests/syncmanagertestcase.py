"""
SyncManager test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import json
import os

from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.core.db import Project
from yokadi.sync.dump import pathForObject
from yokadi.sync.syncmanager import SyncManager
from yokadi.sync.vcsimpl import VcsImpl
from yokadi.tests.yokaditestcase import YokadiTestCase


class StubVcsImpl(VcsImpl):
    def setDir(self, repoDir):
        pass


class SyncManagerTestCase(YokadiTestCase):
    def setUp(self):
        YokadiTestCase.setUp(self)
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()

    def testAdd(self):
        with TemporaryDirectory() as tmpDir:
            syncManager = SyncManager(tmpDir, session=self.session, vcsImpl=StubVcsImpl())
            prj = Project(name="prj")
            self.session.add(prj)
            self.session.commit()

            path = os.path.join(tmpDir, pathForObject(prj))
            self.assertTrue(os.path.exists(path))

    def testUpdate(self):
        with TemporaryDirectory() as tmpDir:
            syncManager = SyncManager(tmpDir, session=self.session, vcsImpl=StubVcsImpl())
            prj = Project(name="prj")
            self.session.add(prj)
            self.session.commit()

            path = os.path.join(tmpDir, pathForObject(prj))

            prj.name = "prj2"
            self.session.commit()

            with open(path) as fp:
                dct = json.load(fp)
                self.assertEqual(dct["name"], "prj2")

    def testDelete(self):
        with TemporaryDirectory() as tmpDir:
            syncManager = SyncManager(tmpDir, session=self.session, vcsImpl=StubVcsImpl())
            prj = Project(name="prj")
            self.session.add(prj)
            self.session.commit()

            path = os.path.join(tmpDir, pathForObject(prj))
            self.assertTrue(os.path.exists(path))

            self.session.delete(prj)
            self.session.commit()
            self.assertFalse(os.path.exists(path))
