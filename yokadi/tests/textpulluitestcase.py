import unittest

from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.tests.pulltestcase import createBothModifiedConflictFixture
from yokadi.tests.pulltestcase import createModifiedDeletedConflictFixture
from yokadi.ycli import tui
from yokadi.ycli.synccmd import TextPullUi
from yokadi.sync import pull


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
            pull.pull(tmpDir, vcsImpl=fixture.vcsImpl, pullUi=TextPullUi())

    def testModifiedDeletedConflict(self):
        with TemporaryDirectory() as tmpDir:
            fixture = createModifiedDeletedConflictFixture(self, tmpDir)

            tui.addInputAnswers("1", "2")
            pull.pull(tmpDir, vcsImpl=fixture.vcsImpl, pullUi=TextPullUi())
