import os

from sqlalchemy import event

from yokadi.sync import DB_SYNC_BRANCH, ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync.dump import clearDump, dump, createVersionFile, \
    commitChanges, deleteObjectDump
from yokadi.sync.pull import pull, importSinceLastSync, importAll


class SyncManager(object):
    def __init__(self, session, dumpDir, vcsImpl=None):
        if vcsImpl is None:
            vcsImpl = GitVcsImpl()
        self.vcsImpl = vcsImpl
        self.dumpDir = dumpDir
        self.vcsImpl.setDir(dumpDir)

        self._deletedObjects = set()

        if session:
            event.listen(session, "after_flush", self._onFlushed)
            event.listen(session, "after_rollback", self._onRollbacked)
            event.listen(session, "after_commit", self._onCommitted)

    def initDumpRepository(self):
        assert not os.path.exists(self.dumpDir)
        os.makedirs(self.dumpDir)
        self.vcsImpl.init()
        createVersionFile(self.dumpDir)
        for dirname in ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME:
            path = os.path.join(self.dumpDir, dirname)
            os.mkdir(path)
        self.commitChanges("Created")

    def clearDump(self):
        clearDump(self.dumpDir)

    def dump(self):
        dump(self.dumpDir, vcsImpl=self.vcsImpl)

    def commitChanges(self, message):
        commitChanges(self.dumpDir, message, vcsImpl=self.vcsImpl)

    def pull(self, pullUi):
        pull(self.dumpDir, vcsImpl=self.vcsImpl, pullUi=pullUi)

    def importSinceLastSync(self, pullUi):
        importSinceLastSync(self.dumpDir, vcsImpl=self.vcsImpl, pullUi=pullUi)

    def importAll(self, pullUi):
        importAll(self.dumpDir, vcsImpl=self.vcsImpl, pullUi=pullUi)

    def push(self):
        self.vcsImpl.push()

    def hasChangesToImport(self):
        changes = self.vcsImpl.getChangesSince(DB_SYNC_BRANCH)
        return changes.hasChanges()

    def hasChangesToPush(self):
        changes = self.vcsImpl.getChangesSince("origin/master")
        return changes.hasChanges()

    def _onFlushed(self, session, *args):
        self._deletedObjects = set(session.deleted)

    def _onCommitted(self, session, *args):
        while self._deletedObjects:
            obj = self._deletedObjects.pop()
            deleteObjectDump(obj, self.dumpDir)

    def _onRollbacked(self, session, *args):
        self._deletedObjects = set()
