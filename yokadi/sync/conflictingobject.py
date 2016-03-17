import json
import os


class ConflictingObject(object):
    """
    Represents a conflict. When the conflict is resolved, self.final must
    contain a dict for the object, or None if the object is to be removed.
    """
    def __init__(self, path, domain, ancestor, local, remote):
        self._path = path
        self.domain = domain
        self.ancestor = ancestor
        self.local = local
        self.remote = remote
        self.final = None

    @staticmethod
    def fromVcsConflict(conflict):
        domain = os.path.dirname(conflict.path)
        ancestor = json.loads(conflict.ancestor)
        local = None if conflict.local is None else json.loads(conflict.local)
        remote = None if conflict.remote is None else json.loads(conflict.remote)
        if local is None or remote is None:
            return ModifiedDeletedConflictingObject(
                    path=conflict.path,
                    domain=domain,
                    ancestor=ancestor,
                    local=local,
                    remote=remote)
        else:
            return BothModifiedConflictingObject(
                    path=conflict.path,
                    domain=domain,
                    ancestor=ancestor,
                    local=local,
                    remote=remote)

    def autoResolve(self):
        raise NotImplementedError()

    def isResolved(self):
        raise NotImplementedError()

    def close(self, vcsImpl):
        assert self.isResolved()
        if self.final is None:
            content = None
        else:
            content = json.dumps(self.final)
        vcsImpl.closeConflict(self._path, content)


class BothModifiedConflictingObject(ConflictingObject):
    """
    Created for conflicts where both remote and local modified the same object,
    but made different changes.

    autoResolve() tries to solve as much conflicts as possible. Remaining
    conflicting keys are kept in self.conflictingKeys. User must then call
    selectValue() to set the value for the conflicting keys.
    """
    def __init__(self, path, domain, ancestor, local, remote):
        ConflictingObject.__init__(self, path, domain, ancestor, local, remote)
        self.conflictingKeys = set(self.ancestor.keys()) | set(self.local.keys()) | set(self.remote.keys())
        self.final = {}

    def autoResolve(self):
        for key in set(self.conflictingKeys):
            ancestor = self.ancestor.get(key, None)
            local = self.local.get(key, None)
            remote = self.remote.get(key, None)
            if local == remote:
                # Not modified
                self.selectValue(key, local)
            elif local == ancestor:
                # Only modified remotely
                self.selectValue(key, remote)
            elif remote == ancestor:
                # Only modified locally
                self.selectValue(key, local)

    def selectValue(self, key, value):
        assert key in self.conflictingKeys
        self.final[key] = value
        self.conflictingKeys.remove(key)

    def isResolved(self):
        return len(self.conflictingKeys) == 0


class ModifiedDeletedConflictingObject(ConflictingObject):
    """
    Created for conflicts where remote removed an object but local modified it
    or vice-versa.
    """
    def __init__(self, path, domain, ancestor, local, remote):
        ConflictingObject.__init__(self, path, domain, ancestor, local, remote)
        self._resolved = False

    def autoResolve(self):
        """
        This kind of conflict cannot be auto-resolved, the user must select
        either the remote or the local version.
        """
        pass

    def isResolved(self):
        return self._resolved

    def selectRemote(self):
        self.final = self.remote
        self._resolved = True

    def selectLocal(self):
        self.final = self.local
        self._resolved = True
