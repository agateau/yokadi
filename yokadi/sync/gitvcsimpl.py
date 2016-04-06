import os
import platform
import subprocess

from yokadi.sync.vcschanges import VcsChanges
from yokadi.sync.vcsconflict import VcsConflict
from yokadi.sync.vcsimpl import VcsImpl
from yokadi.sync.vcsimplerrors import NotFastForwardError, VcsImplError


"""
Output of `git status` is made of two letter strings which can take the
following values in case of conflicts:

UU: unmerged, both modified
Most common: Local and remote modified A in incompatible way.

UD: unmerged, deleted by them
Local updated A. Remote deleted it.

DU: unmerged, deleted by us
Local deleted A. Remote updated it.

DD: unmerged, both deleted
AU: unmerged, added by us
UA: unmerged, added by them
Local renamed A to B. Remote renamed A to C.
Should not happen with guid-based file names since files are never renamed.

AA: unmerged, both added
Both local and remote created A.
Should not happen with guid-based file names since files are never renamed.
"""
CONFLICT_STATES = set(["DD", "AU", "UD", "UA", "DU", "AA", "UU"])


class GitVcsImpl(VcsImpl):
    name = "Git"

    def setDir(self, srcDir):
        self._srcDir = srcDir

    def isValidVcsDir(self):
        gitDir = os.path.join(self._srcDir, ".git")
        return os.path.exists(gitDir)

    def init(self):
        self._run("init")
        self._ensureUserInfoIsSet()

    def isWorkTreeClean(self):
        return len(list(self._getStatus())) == 0

    def commitAll(self, message=None):
        if message is None:
            message = "Synced"
        self._run("add", ".")
        self._run("commit", "-m", message)

    def clone(self, remoteUrl):
        parentDir = os.path.dirname(self._srcDir)
        cloneDir = os.path.basename(self._srcDir)
        self._run("clone", "--quiet", remoteUrl, cloneDir, cwd=parentDir)
        self._ensureUserInfoIsSet()

    def pull(self):
        self._run("fetch", "--quiet")

        commitMessage = "Merged"
        # Force a high rename-threshold: we are not interested in finding renames
        try:
            self._run("merge", "--quiet", "--strategy", "recursive",
                               "--strategy-option", "rename-threshold=100%",
                               "-m", commitMessage,
                               "FETCH_HEAD",)
            return True
        except subprocess.CalledProcessError as exc:
            if exc.returncode == 1:
                # Merge failed because of conflicts
                return False
            raise VcsImplError.fromSubprocessError(exc)

    def push(self):
        try:
            self._run("push", "--quiet", "origin", "master:master")
        except subprocess.CalledProcessError as exc:
            if exc.returncode == 1:
                raise NotFastForwardError.fromSubprocessError(exc)
            else:
                raise VcsImplError.fromSubprocessError(exc)

    def hasConflicts(self):
        for status, path in self._getStatus():
            if status in CONFLICT_STATES:
                return True
        return False

    def getConflicts(self):
        for status, path in self._getStatus():
            if status in CONFLICT_STATES:
                ancestor = self.getFileContentAt(path, ":1")
                if status[0] == "D":
                    local = None
                else:
                    local = self.getFileContentAt(path, ":2")
                if status[1] == "D":
                    remote = None
                else:
                    remote = self.getFileContentAt(path, ":3")
                yield VcsConflict(path=path, ancestor=ancestor, local=local, remote=remote)

    def abortMerge(self):
        self._run("merge", "--abort")

    def getChangesSince(self, commitId):
        output = self._run("diff", "--name-status", commitId + "..").decode("utf-8")
        changes = VcsChanges()
        for line in output.splitlines():
            status, filename = line.split()
            if status == "M":
                changes.modified.add(filename)
            elif status == "A":
                changes.added.add(filename)
            elif status == "D":
                changes.removed.add(filename)
            else:
                raise Exception("Unknown status {} in line '{}'".format(status, line))
        return changes

    def updateBranch(self, branchName, commitId):
        self._run("branch", "--force", branchName, commitId)

    def getFileContentAt(self, filePath, commitId):
        return self._run("show", commitId + ":" + filePath)

    def getTrackedFiles(self):
        return [x for x in self._run("ls-files").decode("utf-8").split("\n") if x]

    def _run(self, *args, **kwargs):
        cwd = kwargs.get("cwd", self._srcDir)
        cmd = ["git", "-C", cwd]
        cmd.extend(args)
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)

    def _ensureUserInfoIsSet(self):
        username = self._getConfig("user", "name")
        email = self._getConfig("user", "email")
        if username and email:
            return

        hostname = platform.node()
        if not hostname:
            hostname = "example.com"
        if not username:
            username = os.environ.get("USER", "user")
            self._setConfig("user", "name", username)
        if not email:
            email = username + "@" + hostname
            self._setConfig("user", "email", email)

    def _getConfig(self, section, key):
        try:
            return self._run("config", section + "." + key)
        except subprocess.CalledProcessError as exc:
            if exc.returncode == 1:
                # Key does not exist
                return None
            raise exc

    def _setConfig(self, section, key, value):
        self._run("config", section + "." + key, value)

    def _getStatus(self):
        output = self._run("status", "--porcelain").decode("utf-8")
        for line in output.splitlines():
            status = line[:2]
            path = line[3:].strip()
            yield status, path
