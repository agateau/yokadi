import textwrap
import unittest

from contextlib import redirect_stdout
from io import StringIO
from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.ycli.synccmd import SyncCmd, TextPullUi


class SyncCmdTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

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
