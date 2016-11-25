"""
DbReplicator
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os

from sqlalchemy import event

from yokadi.sync.dump import isDumpableObject, getLinkedObject, dumpObjectDict, pathForObject, dictFromObject


class DbReplicator:
    """
    Monitors db events and replicate changes on the filesystem
    """
    def __init__(self, dumpDir, session):
        self._pathsToDelete = set()
        self._dictsToWrite = {}
        self.dumpDir = dumpDir

        event.listen(session, "after_flush", self._onFlushed)
        event.listen(session, "after_rollback", self._onRollbacked)
        event.listen(session, "after_commit", self._onCommitted)
        self.session = session

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

            dct = dictFromObject(obj)
            self._dictsToWrite[pathForObject(obj)] = dct

    def _onCommitted(self, session, *args):
        for path in self._pathsToDelete:
            fullPath = os.path.join(self.dumpDir, path)
            if os.path.exists(fullPath):
                os.unlink(fullPath)

        for path, dct in self._dictsToWrite.items():
            if path in self._pathsToDelete:
                continue
            dumpObjectDict(dct, os.path.join(self.dumpDir, os.path.dirname(path)))

    def _onRollbacked(self, session, *args):
        self._pathsToDelete = set()
        self._dictsToWrite = dict()
