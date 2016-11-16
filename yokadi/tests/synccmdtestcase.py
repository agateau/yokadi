"""
SyncCmd test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os
import textwrap

from contextlib import redirect_stdout
from io import StringIO
from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.sync import TASKS_DIRNAME
from yokadi.ycli.main import YokadiCmd
from yokadi.ycli.synccmd import SyncCmd, TextPullUi
from yokadi.tests.yokaditestcase import YokadiTestCase


class SyncCmdTestCase(YokadiTestCase):
    def setUp(self):
        YokadiTestCase.setUp(self)
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()
        self.cmd = YokadiCmd()

    def test_printPullResults(self):
        textPullUi = TextPullUi()
        textPullUi.addRename("projects", "foo", "foo_1")
        textPullUi.addRename("projects", "bar", "bar_1")
        textPullUi.addRename("projects", "baz", "baz_1")

        with TemporaryDirectory() as tmpDir:
            out = StringIO()
            with redirect_stdout(out):
                cmd = SyncCmd(dumpDir=tmpDir)
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
        self.assertFalse(os.path.exists(self.cmd.dumpDir))

    def testTaskIsDumpedIfInitialized(self):
        os.makedirs(self.cmd.dumpDir)

        # Recreate cmd *after* creating the dump dir to simulate starting
        # Yokadi with an existing dump dir
        self.cmd = YokadiCmd()

        t1 = dbutils.addTask("x", "t1", interactive=False)
        self.session.commit()
        path = os.path.join(self.cmd.dumpDir, TASKS_DIRNAME, t1.uuid + ".json")
        self.assertTrue(os.path.exists(path))

    def testTaskIsDumpedIfInitializedLater(self):
        t1 = dbutils.addTask("x", "t1", interactive=False)
        self.session.commit()
        self.cmd.do_s_init("")
        # t1 should be dumped by s_init
        path = os.path.join(self.cmd.dumpDir, TASKS_DIRNAME, t1.uuid + ".json")
        self.assertTrue(os.path.exists(path), "Existing task not dumped")

        # t2 should be dumped by the syncmanager watching events
        t2 = dbutils.addTask("x", "t2", interactive=False)
        self.session.commit()
        path = os.path.join(self.cmd.dumpDir, TASKS_DIRNAME, t2.uuid + ".json")
        self.assertTrue(os.path.exists(path), "New task not dumped")
