"""
Test cases for TextPullUi

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import textwrap

from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.tests.pulltestcase import createBothModifiedConflictFixture
from yokadi.tests.pulltestcase import createModifiedDeletedConflictFixture
from yokadi.ycli import tui
from yokadi.ycli.synccmd import TextPullUi, shortenText, SHORTENED_SUFFIX, SHORTENED_TEXT_MAX_LENGTH
from yokadi.sync import ALIASES_DIRNAME
from yokadi.sync.syncmanager import SyncManager
from yokadi.tests.yokaditestcase import YokadiTestCase


class TextPullUiTestCase(YokadiTestCase):
    def setUp(self):
        YokadiTestCase.setUp(self)
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
            syncManager = SyncManager(vcsImpl=fixture.vcsImpl)
            syncManager.pull(pullUi=TextPullUi())

    def testModifiedDeletedConflict(self):
        with TemporaryDirectory() as tmpDir:
            fixture = createModifiedDeletedConflictFixture(self, tmpDir)

            tui.addInputAnswers("1", "2")
            syncManager = SyncManager(vcsImpl=fixture.vcsImpl)
            syncManager.pull(pullUi=TextPullUi())

    def testAddRename(self):
        textPullUi = TextPullUi()
        textPullUi.addRename(ALIASES_DIRNAME, "a", "a_1")
        textPullUi.addRename(ALIASES_DIRNAME, "b", "b_1")

        renames = textPullUi.getRenames()
        self.assertEqual(renames, {
            ALIASES_DIRNAME: [("a", "a_1"), ("b", "b_1")]
            })

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
            ),
            (None, None),
        )

        for src, expected in data:
            output = shortenText(src)
            self.assertEqual(output, expected)
