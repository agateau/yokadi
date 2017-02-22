"""
Test cases for the SyncManager class
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from yokadi.core import db
from yokadi.sync import VERSION
from yokadi.sync.syncmanager import SyncManager
from yokadi.sync.vcsimpl import VcsImpl
from yokadi.tests.yokaditestcase import YokadiTestCase
from yokadi.tests.stubpullui import StubPullUi
from yokadi.tests.stubvcsimpl import StubVcsImpl


class SyncManagerTestCase(YokadiTestCase):
    def setUp(self):
        YokadiTestCase.setUp(self)
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

    def testCheckDumpVersion(self):
        class MyVcsImpl(VcsImpl):
            def __init__(self):
                self.fakeVersion = 0

            def srcDir(self):
                return ""

            def getFileContentAt(self, filePath, commitId):
                return str(self.fakeVersion)

        vcsImpl = MyVcsImpl()
        syncManager = SyncManager(vcsImpl=vcsImpl)

        vcsImpl.fakeVersion = VERSION - 1
        self.assertFalse(syncManager._checkDumpVersion(pullUi=StubPullUi()))

        vcsImpl.fakeVersion = VERSION + 1
        self.assertFalse(syncManager._checkDumpVersion(pullUi=StubPullUi()))

        vcsImpl.fakeVersion = VERSION
        self.assertTrue(syncManager._checkDumpVersion(pullUi=StubPullUi()))

    def testPullReturnsTrue(self):
        syncManager = SyncManager(session=self.session, vcsImpl=StubVcsImpl())
        ok = syncManager.pull(pullUi=StubPullUi())
        self.assertTrue(ok)
