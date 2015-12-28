# -*- coding: UTF-8 -*-
"""
Basepaths test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os
import shutil
import tempfile
import unittest

from pathlib import Path

from yokadi.core import basepaths


def saveEnv():
    return dict(os.environ)


def restoreEnv(env):
    os.environ = env


class BasePathsUnixTestCase(unittest.TestCase):
    def setUp(self):
        self._oldWindows = basepaths._WINDOWS
        basepaths._WINDOWS = False

        self._oldEnv = saveEnv()
        self.testHomeDir = tempfile.mkdtemp(prefix="yokadi-basepaths-testcase")
        os.environ["HOME"] = self.testHomeDir

    def tearDown(self):
        shutil.rmtree(self.testHomeDir)
        restoreEnv(self._oldEnv)
        basepaths._WINDOWS = self._oldWindows

    def testMigrateOldDb(self):
        oldDb = Path(self.testHomeDir) / '.yokadi.db'
        newDb = Path(basepaths.getDbPath())

        oldDb.touch()

        basepaths.migrateOldDb()
        self.assertFalse(oldDb.exists())
        self.assertTrue(newDb.exists())

    def testMigrateNothingToDo(self):
        newDb = Path(basepaths.getDbPath())
        basepaths.migrateOldDb()
        basepaths.migrateOldHistory()
        self.assertFalse(newDb.exists())

    def testMigrateOldDbFails(self):
        oldDb = Path(self.testHomeDir) / '.yokadi.db'
        newDb = Path(basepaths.getDbPath())

        oldDb.touch()
        newDb.parent.mkdir(parents=True)
        newDb.touch()

        self.assertRaises(basepaths.MigrationException, basepaths.migrateOldDb)

    def testMigrateOldHistory(self):
        old = Path(self.testHomeDir) / '.yokadi_history'
        new = Path(basepaths.getHistoryPath())

        old.touch()

        basepaths.migrateOldHistory()
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())

    def testMigrateOldHistoryOverwriteNew(self):
        old = Path(self.testHomeDir) / '.yokadi_history'
        new = Path(basepaths.getHistoryPath())

        with old.open('w') as f:
            f.write('old')
        new.parent.mkdir(parents=True)
        with new.open('w') as f:
            f.write('new')

        basepaths.migrateOldHistory()
        self.assertFalse(old.exists())
        with new.open() as f:
            newData = f.read()
        self.assertEqual(newData, 'old')

    def testHistoryEnvVar(self):
        path = "foo"
        os.environ["YOKADI_HISTORY"] = path
        self.assertEqual(basepaths.getHistoryPath(), path)

    def testDbEnvVar(self):
        path = "foo"
        os.environ["YOKADI_DB"] = path
        self.assertEqual(basepaths.getDbPath(), path)


class BasePathsWindowsTestCase(unittest.TestCase):
    def setUp(self):
        self._oldWindows = basepaths._WINDOWS
        self._oldEnv = saveEnv()
        basepaths._WINDOWS = True
        self.testAppDataDir = tempfile.mkdtemp(prefix="yokadi-basepaths-testcase")
        os.environ["APPDATA"] = self.testAppDataDir

    def tearDown(self):
        shutil.rmtree(self.testAppDataDir)
        basepaths._WINDOWS = self._oldWindows
        restoreEnv(self._oldEnv)

    def testGetCacheDir(self):
        expected = os.path.join(self.testAppDataDir, "yokadi", "cache")
        self.assertEqual(basepaths.getCacheDir(), expected)

    def testGetDataDir(self):
        expected = os.path.join(self.testAppDataDir, "yokadi", "data")
        self.assertEqual(basepaths.getDataDir(), expected)

    def testOldHistoryPath(self):
        expected = os.path.join(self.testAppDataDir, ".yokadi_history")
        self.assertEqual(basepaths._getOldHistoryPath(), expected)
