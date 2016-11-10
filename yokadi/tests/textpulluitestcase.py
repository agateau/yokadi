import textwrap
import unittest

from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.tests.pulltestcase import createBothModifiedConflictFixture
from yokadi.tests.pulltestcase import createModifiedDeletedConflictFixture
from yokadi.ycli import tui
from yokadi.ycli.synccmd import TextPullUi, prepareConflictText, shortenText, SHORTENED_SUFFIX, \
        SHORTENED_TEXT_MAX_LENGTH
from yokadi.sync import ALIASES_DIRNAME
from yokadi.sync.syncmanager import SyncManager


class TextPullUiTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

    def testPullBothModifiedConflict(self):
        with TemporaryDirectory() as tmpDir:
            fixture = createBothModifiedConflictFixture(self, self.session, tmpDir,
                localChanges=dict(
                    title="Local title",
                    description="Local description"
                ),
                remoteChanges=dict(
                    title="Remote title",
                    description="Remote description"
                ))

            tui.addInputAnswers("1", "2")
            syncManager = SyncManager(tmpDir, fixture.vcsImpl)
            syncManager.pull(pullUi=TextPullUi())

    def testModifiedDeletedConflict(self):
        with TemporaryDirectory() as tmpDir:
            fixture = createModifiedDeletedConflictFixture(self, tmpDir)

            tui.addInputAnswers("1", "2")
            syncManager = SyncManager(tmpDir, fixture.vcsImpl)
            syncManager.pull(pullUi=TextPullUi())

    def testAddRename(self):
        textPullUi = TextPullUi()
        textPullUi.addRename(ALIASES_DIRNAME, "a", "a_1")
        textPullUi.addRename(ALIASES_DIRNAME, "b", "b_1")

        renames = textPullUi.getRenames()
        self.assertEqual(renames, {
            ALIASES_DIRNAME: [("a", "a_1"), ("b", "b_1")]
            })

    def testPrepareConflictText(self):
        data = (
            ("foo", "bar", "L> foo\nR> bar\n"),
            (
                textwrap.dedent("""\
                    Common
                    Local1
                    More common
                    Local2
                    Local3
                    Even more common"""),
                textwrap.dedent("""\
                    Common
                    Remote1
                    More common
                    Remote2
                    Even more common"""),
                textwrap.dedent("""\
                    Common
                    L> Local1
                    R> Remote1
                    More common
                    R> Remote2
                    L> Local2
                    L> Local3
                    Even more common
                    """),
            )
        )

        for local, remote, expected in data:
            output = prepareConflictText(local, remote)
            self.assertEqual(output, expected)

    def testShortenText(self):
        data = (
            ("foo", "foo"),
            (
                textwrap.dedent("""\
                    Common
                    Local1
                    More common
                    Local2
                    Local3
                    Even more common"""),
                "Common" + SHORTENED_SUFFIX
            ),
            (
                "a" * 160,
                "a" * (SHORTENED_TEXT_MAX_LENGTH - len(SHORTENED_SUFFIX)) + SHORTENED_SUFFIX
            )
        )

        for src, expected in data:
            output = shortenText(src)
            self.assertEqual(output, expected)
