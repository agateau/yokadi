import os

from sqlalchemy import event

from yokadi.sync import DB_SYNC_BRANCH, ALIASES_DIRNAME, PROJECTS_DIRNAME, \
        TASKS_DIRNAME
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync.dump import clearDump, dump, createVersionFile, \
        commitChanges, isDumpableObject, getLinkedObject, dumpObjectDict, \
        pathForObject, dirnameForObject, dictFromObject

from yokadi.sync.pull import pull, importSinceLastSync, importAll


class SyncManager(object):
    def __init__(self, session, dumpDir, vcsImpl=None):
        if vcsImpl is None:
            vcsImpl = GitVcsImpl()
        self.vcsImpl = vcsImpl
        self.dumpDir = dumpDir
        self.vcsImpl.setDir(dumpDir)

        self._pathsToDelete = set()
        self._dictsToWrite = {}

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

    def hasChangesToCommit(self):
        return not self.vcsImpl.isWorkTreeClean()

    def hasChangesToImport(self):
        changes = self.vcsImpl.getChangesSince(DB_SYNC_BRANCH)
        return changes.hasChanges()

    def hasChangesToPush(self):
        changes = self.vcsImpl.getChangesSince("origin/master")
        return changes.hasChanges()

    def _onFlushed(self, session, *args):
        for obj in session.deleted:
            if not isDumpableObject(obj):
                continue
            if getLinkedObject(obj):
                continue
            self._pathsToDelete.add(pathForObject(obj))
        for obj in session.dirty | session.new:
            if not isDumpableObject(obj):
                continue
            linkedObject = getLinkedObject(obj)
            if linkedObject:
                obj = linkedObject

            key = (dirnameForObject(obj), obj.uuid)
            dct = dictFromObject(obj)

            self._dictsToWrite[key] = dct

    def _onCommitted(self, session, *args):
        for path in self._pathsToDelete:
            fullPath = os.path.join(self.dumpDir, path)
            if os.path.exists(fullPath):
                os.unlink(fullPath)

        for (dirname, _), dct in self._dictsToWrite.items():
            dumpObjectDict(dct, os.path.join(self.dumpDir, dirname))

    def _onRollbacked(self, session, *args):
        self._pathsToDelete = set()
