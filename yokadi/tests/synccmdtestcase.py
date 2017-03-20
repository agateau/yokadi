"""
SyncCmd test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os
import textwrap

from contextlib import redirect_stdout
from io import StringIO

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.core.yokadiexception import YokadiException
from yokadi.sync import TASKS_DIRNAME
from yokadi.ycli.synccmd import SyncCmd, TextPullUi
from yokadi.tests.yokaditestcase import YokadiTestCase


class SyncCmdTestCase(YokadiTestCase):
    def setUp(self):
        YokadiTestCase.setUp(self)
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

    def test_printPullResults(self):
        textPullUi = TextPullUi()
        textPullUi.addRename("projects", "foo", "foo_1")
        textPullUi.addRename("projects", "bar", "bar_1")
        textPullUi.addRename("projects", "baz", "baz_1")

        out = StringIO()
        with redirect_stdout(out):
            cmd = SyncCmd()
            cmd._printPullResults(textPullUi)
            content = out.getvalue()
            self.assertEqual(content, textwrap.dedent("""\
                Elements renamed in projects
                - foo => foo_1
                - bar => bar_1
                - baz => baz_1
                """))

    def testNothingIsDumpedIfNotInitialized(self):
        dbutils.addTask("x", "t1", interactive=False)
        self.session.commit()
        cmd = SyncCmd()
        self.assertFalse(os.path.exists(cmd._dumpDir))

    def testTaskIsDumpedIfInitialized(self):
        dumpDir = SyncCmd()._dumpDir

        os.makedirs(dumpDir)

        # Create cmd *after* creating the dump dir to simulate starting Yokadi
        # with an existing dump dir
        cmd = SyncCmd(dumpDir=dumpDir)  # noqa

        t1 = dbutils.addTask("x", "t1", interactive=False)
        self.session.commit()
        path = os.path.join(dumpDir, TASKS_DIRNAME, t1.uuid + ".json")
        self.assertTrue(os.path.exists(path))

    def testTaskIsDumpedIfInitializedLater(self):
        t1 = dbutils.addTask("x", "t1", interactive=False)
        self.session.commit()

        cmd = SyncCmd()
        dumpDir = cmd._dumpDir
        cmd.do_s_init("")
        # t1 should be dumped by s_init
        path = os.path.join(dumpDir, TASKS_DIRNAME, t1.uuid + ".json")
        self.assertTrue(os.path.exists(path), "Existing task not dumped")

        # t2 should be dumped by the syncmanager watching events
        t2 = dbutils.addTask("x", "t2", interactive=False)
        self.session.commit()
        path = os.path.join(dumpDir, TASKS_DIRNAME, t2.uuid + ".json")
        self.assertTrue(os.path.exists(path), "New task not dumped")

    def testSyncWhenNotInitialized(self):
        # Trying to use a sync command if not initialized should raise a
        # YokadiException to show a user-friendly message
        cmd = SyncCmd()
        self.assertRaises(YokadiException, cmd.do_s_sync, "")
