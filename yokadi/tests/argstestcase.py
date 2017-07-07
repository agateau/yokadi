"""
Command line argument test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os

from argparse import ArgumentParser
from tempfile import TemporaryDirectory

from yokadi.tests.yokaditestcase import YokadiTestCase

from yokadi.core import basepaths
from yokadi.ycli import commonargs


def parseArgs(argv):
    parser = ArgumentParser()
    commonargs.addArgs(parser)
    return parser.parse_args(argv)


class ArgsTestCase(YokadiTestCase):
    def setUp(self):
        super().setUp()
        self.defaultDataDir = basepaths.getDataDir()
        self.defaultDbPath = basepaths.getDbPath(self.defaultDataDir)

    def testNoArguments(self):
        args = parseArgs([])
        dataDir, dbPath = commonargs.processArgs(args)
        self.assertEqual(dataDir, self.defaultDataDir)
        self.assertEqual(dbPath, self.defaultDbPath)

        self.assertTrue(os.path.isdir(dataDir))
        self.assertTrue(os.path.isdir(os.path.dirname(dbPath)))

    def testDataDir(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            args = parseArgs(["--datadir", tmpDir])
            dataDir, dbPath = commonargs.processArgs(args)
            self.assertEqual(dataDir, tmpDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, basepaths.DB_NAME))

    def testRelativeDataDir(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            os.chdir(tmpDir)
            args = parseArgs(["--datadir", "."])
            dataDir, dbPath = commonargs.processArgs(args)
            self.assertEqual(dataDir, tmpDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, basepaths.DB_NAME))

    def testDataDirDoesNotExist(self):
        args = parseArgs(["--datadir", "/does/not/exist"])
        self.assertRaises(SystemExit, commonargs.processArgs, args)

    def testCantUseBothDataDirAndDb(self):
        self.assertRaises(SystemExit, parseArgs, ["--datadir", "foo", "--db", "bar"])

    def testDb(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            args = parseArgs(["--db", os.path.join(tmpDir, "foo.db")])
            dataDir, dbPath = commonargs.processArgs(args)
            self.assertEqual(dataDir, self.defaultDataDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, "foo.db"))

    def testRelativeDb(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            os.chdir(tmpDir)
            args = parseArgs(["--db", "foo.db"])
            dataDir, dbPath = commonargs.processArgs(args)
            self.assertEqual(dataDir, self.defaultDataDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, "foo.db"))

    def testDbDirDoesNotExist(self):
        args = parseArgs(["--db", "/does/not/exist/foo.db"])
        self.assertRaises(SystemExit, commonargs.processArgs, args)

    def testArgsOverrideEnvVar(self):
        with TemporaryDirectory(prefix="yokadi-tests-") as tmpDir:
            os.environ["YOKADI_DB"] = os.path.join(tmpDir, "env.db")
            os.chdir(tmpDir)
            args = parseArgs(["--db", "arg.db"])
            dataDir, dbPath = commonargs.processArgs(args)
            self.assertEqual(dataDir, self.defaultDataDir)
            self.assertEqual(dbPath, os.path.join(tmpDir, "arg.db"))
