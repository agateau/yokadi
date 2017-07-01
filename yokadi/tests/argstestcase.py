"""
Command line argument test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os

from tempfile import TemporaryDirectory

from yokadi.tests.yokaditestcase import YokadiTestCase

from yokadi.core import basepaths
from yokadi.ycli.main import processArgs


class ArgsTestCase(YokadiTestCase):
    def setUp(self):
        super().setUp()
        self.defaultDataDir = basepaths.getDataDir()
        self.defaultDbPath = basepaths.getDbPath(self.defaultDataDir)

    def testNoArguments(self):
        _, dataDir, dbPath = processArgs([])
        self.assertEqual(dataDir, self.defaultDataDir)
        self.assertEqual(dbPath, self.defaultDbPath)

        self.assertTrue(os.path.isdir(dataDir))
        self.assertTrue(os.path.isdir(os.path.dirname(dbPath)))

    def testDataDir(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            _, dataDir, dbPath = processArgs(["--datadir", tmpDir])
            self.assertEqual(dataDir, tmpDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, basepaths.DB_NAME))

    def testRelativeDataDir(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            os.chdir(tmpDir)
            _, dataDir, dbPath = processArgs(["--datadir", "."])
            self.assertEqual(dataDir, tmpDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, basepaths.DB_NAME))

    def testDataDirDoesNotExist(self):
        self.assertRaises(SystemExit, processArgs, ["--datadir", "/does/not/exist"])

    def testCantUseBothDataDirAndDb(self):
        self.assertRaises(SystemExit, processArgs, ["--datadir", "foo", "--db", "bar"])

    def testDb(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            _, dataDir, dbPath = processArgs(["--db", os.path.join(tmpDir, "foo.db")])
            self.assertEqual(dataDir, self.defaultDataDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, "foo.db"))

    def testRelativeDb(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            os.chdir(tmpDir)
            _, dataDir, dbPath = processArgs(["--db", "foo.db"])
            self.assertEqual(dataDir, self.defaultDataDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, "foo.db"))

    def testDbDirDoesNotExist(self):
        self.assertRaises(SystemExit, processArgs, ["--db", "/does/not/exist/foo.db"])

    def testArgsOverrideEnvVar(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            os.environ["YOKADI_DB"] = os.path.join(tmpDir, "env.db")
            os.chdir(tmpDir)
            _, dataDir, dbPath = processArgs(["--db", "arg.db"])
            self.assertEqual(dataDir, self.defaultDataDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, "arg.db"))
