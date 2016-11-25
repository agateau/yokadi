"""
ConflictingObject test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import json

from yokadi.sync.conflictingobject import ConflictingObject, ModifiedDeletedConflictingObject, \
        BothModifiedConflictingObject
from yokadi.sync.vcsconflict import VcsConflict
from yokadi.sync.vcsimpl import VcsImpl
from yokadi.tests.yokaditestcase import YokadiTestCase


class StubVcsImpl(VcsImpl):
    def closeConflict(self, path, content):
        self.path = path
        self.content = content


def createConflict(*, path="testpath", ancestor=None, local=None, remote=None):
    def prepare(dct):
        if dct is None:
            return None
        return json.dumps(dct).encode("utf-8")
    return VcsConflict(path=path, ancestor=prepare(ancestor), local=prepare(local), remote=prepare(remote))


class ConflictingObjectTestCase(YokadiTestCase):
    def testModifiedDeleted_keepDeleted(self):
        conflict = createConflict(ancestor=dict(a=1), local=dict(a=2), remote=None)
        conflictingObject = ConflictingObject.fromVcsConflict(conflict)

        self.assertTrue(isinstance(conflictingObject, ModifiedDeletedConflictingObject))
        self.assertFalse(conflictingObject.isResolved())

        conflictingObject.selectRemote()
        self.assertTrue(conflictingObject.isResolved())

        vcsImpl = StubVcsImpl()
        conflictingObject.close(vcsImpl)
        self.assertIsNone(vcsImpl.content)

    def testModifiedDeleted_keepModified(self):
        conflict = createConflict(ancestor=dict(a=1), local=dict(a=2), remote=None)
        conflictingObject = ConflictingObject.fromVcsConflict(conflict)

        self.assertTrue(isinstance(conflictingObject, ModifiedDeletedConflictingObject))
        self.assertFalse(conflictingObject.isResolved())

        conflictingObject.selectLocal()
        self.assertTrue(conflictingObject.isResolved())

        vcsImpl = StubVcsImpl()
        conflictingObject.close(vcsImpl)
        self.assertEqual(json.loads(vcsImpl.content.decode("utf-8")), dict(a=2))

    def testBothModified(self):
        conflict = createConflict(ancestor=dict(a="a"), local=dict(a="l"), remote=dict(a="r"))
        conflictingObject = ConflictingObject.fromVcsConflict(conflict)

        self.assertTrue(isinstance(conflictingObject, BothModifiedConflictingObject))
        self.assertFalse(conflictingObject.isResolved())

        conflictingObject.selectValue("a", "m")
        self.assertTrue(conflictingObject.isResolved())

        vcsImpl = StubVcsImpl()
        conflictingObject.close(vcsImpl)
        self.assertEqual(json.loads(vcsImpl.content.decode("utf-8")), dict(a="m"))

    def testBothModified_autoResolve(self):
        conflict = createConflict(ancestor=dict(localEqRemote="old", onlyModRemotely="old", onlyModLocally="old"),
                                  local=dict(localEqRemote="leq", onlyModRemotely="old", onlyModLocally="local"),
                                  remote=dict(localEqRemote="leq", onlyModRemotely="remote", onlyModLocally="old"))
        conflictingObject = ConflictingObject.fromVcsConflict(conflict)

        self.assertTrue(isinstance(conflictingObject, BothModifiedConflictingObject))
        self.assertFalse(conflictingObject.isResolved())

        conflictingObject.autoResolve()
        self.assertTrue(conflictingObject.isResolved())

        vcsImpl = StubVcsImpl()
        conflictingObject.close(vcsImpl)
        self.assertEqual(json.loads(vcsImpl.content.decode("utf-8")),
                         dict(localEqRemote="leq", onlyModRemotely="remote", onlyModLocally="local"))

    def testBothModified_noAncestor(self):
        conflict = createConflict(ancestor=None, local=dict(a="l"), remote=dict(a="r"))
        conflictingObject = ConflictingObject.fromVcsConflict(conflict)

        self.assertTrue(isinstance(conflictingObject, BothModifiedConflictingObject))
        self.assertFalse(conflictingObject.isResolved())

        conflictingObject.selectValue("a", "m")
        self.assertTrue(conflictingObject.isResolved())

        vcsImpl = StubVcsImpl()
        conflictingObject.close(vcsImpl)
        self.assertEqual(json.loads(vcsImpl.content.decode("utf-8")), dict(a="m"))
