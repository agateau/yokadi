import unittest

from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.tests.pulltestcase import createBothModifiedConflictFixture
from yokadi.tests.pulltestcase import createModifiedDeletedConflictFixture
from yokadi.ycli import tui
from yokadi.ycli.synccmd import TextPullUi
from yokadi.sync.pullui import PullUi
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

    def testGetMergeStrategy(self):
        localProject = db.Project(name="local")
        remoteProject = db.Project(name="remote")

        textPullUi = TextPullUi()
        for answer, expectedStrategy in (("1", PullUi.MERGE), ("2", PullUi.RENAME), ("3", PullUi.CANCEL)):
            tui.addInputAnswers(answer)
            strategy = textPullUi.getMergeStrategy(localProject, remoteProject)
            self.assertEqual(strategy, expectedStrategy)

    def testAddRename(self):
        textPullUi = TextPullUi()
        textPullUi.addRename(ALIASES_DIRNAME, "a", "a_1")
        textPullUi.addRename(ALIASES_DIRNAME, "b", "b_1")

        renames = textPullUi.getRenames()
        self.assertEqual(renames, {
            ALIASES_DIRNAME: [("a", "a_1"), ("b", "b_1")]
            })
