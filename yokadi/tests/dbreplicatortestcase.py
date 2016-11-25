"""
DbReplicator test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import json
import os

from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.core.db import Project
from yokadi.sync.dbreplicator import DbReplicator
from yokadi.sync.dump import pathForObject
from yokadi.tests.yokaditestcase import YokadiTestCase


class DbReplicatorTestCase(YokadiTestCase):
    def setUp(self):
        YokadiTestCase.setUp(self)
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()

    def testAdd(self):
        with TemporaryDirectory() as tmpDir:
            dbReplicator = DbReplicator(tmpDir, self.session)
            prj = Project(name="prj")
            self.session.add(prj)
            self.session.commit()

            path = os.path.join(tmpDir, pathForObject(prj))
            self.assertTrue(os.path.exists(path))

    def testUpdate(self):
        with TemporaryDirectory() as tmpDir:
            dbReplicator = DbReplicator(tmpDir, self.session)
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
            dbReplicator = DbReplicator(tmpDir, self.session)
            prj = Project(name="prj")
            self.session.add(prj)
            self.session.commit()

            path = os.path.join(tmpDir, pathForObject(prj))
            self.assertTrue(os.path.exists(path))

            self.session.delete(prj)
            self.session.commit()
            self.assertFalse(os.path.exists(path))

    def testRollback_add(self):
        with TemporaryDirectory() as tmpDir:
            dbReplicator = DbReplicator(tmpDir, self.session)
            prj = Project(name="prj")
            self.session.add(prj)
            self.session.flush()

            self.session.rollback()
            self.session.commit()

            path = os.path.join(tmpDir, pathForObject(prj))
            self.assertFalse(os.path.exists(path))

    def testRollback_update(self):
        with TemporaryDirectory() as tmpDir:
            dbReplicator = DbReplicator(tmpDir, self.session)
            prj = Project(name="prj")
            self.session.add(prj)
            self.session.commit()

            path = os.path.join(tmpDir, pathForObject(prj))
            self.assertTrue(os.path.exists(path))

            prj.name = "newprj"
            self.session.rollback()
            self.session.commit()
            with open(path) as fp:
                dct = json.load(fp)
            self.assertEqual(dct["name"], "prj")

    def testRollback_delete(self):
        with TemporaryDirectory() as tmpDir:
            dbReplicator = DbReplicator(tmpDir, self.session)
            prj = Project(name="prj")
            self.session.add(prj)
            self.session.commit()

            path = os.path.join(tmpDir, pathForObject(prj))
            self.assertTrue(os.path.exists(path))

            self.session.delete(prj)
            self.session.rollback()
            self.session.commit()
            self.assertTrue(os.path.exists(path))
