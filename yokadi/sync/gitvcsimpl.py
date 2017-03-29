"""
Implementation of VcsImpl using Git

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os
import platform
import subprocess

from yokadi.sync.vcschanges import VcsChanges
from yokadi.sync.vcsconflict import VcsConflict
from yokadi.sync.vcsimpl import VcsImpl
from yokadi.sync.vcsimplerrors import NotFastForwardError, VcsImplError, CantCommitWithConflictsError


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
Can happen if repositories for two identical database were created independently.
"""
CONFLICT_STATES = set(["DD", "AU", "UD", "UA", "DU", "AA", "UU"])


class GitSubprocessError(VcsImplError):
    """
    Wraps a subprocess.CalledProcessError to show stdout in the message.
    """
    def __init__(self, error):
        output = error.output.decode('utf-8', 'replace')
        Exception.__init__(self, "Command {} failed with error code {}. Output:\n{}" \
            .format(error.cmd, error.returncode, output))
        self.returncode = error.returncode


def _parseStatusOutput(output):
    changes = VcsChanges()
    for line in output.splitlines():
        status, filename = line.split()
        if status == "M":
            changes.modified.add(filename)
        elif status == "A" or status == "??":
            changes.added.add(filename)
        elif status == "D":
            changes.removed.add(filename)
        else:
            raise Exception("Unknown status {} in line '{}'".format(status, line))
    return changes


class GitVcsImpl(VcsImpl):
    name = "Git"
    def __init__(self, srcDir):
        self._srcDir = srcDir

    @property
    def srcDir(self):
        return self._srcDir

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
        if self.hasConflicts():
            raise CantCommitWithConflictsError()
        # Use --all to keep Travis git (1.8.5.6) happy
        self._run("add", "--all", ".")
        self._run("commit", "-m", message)

    def clone(self, remoteUrl):
        parentDir = os.path.dirname(self._srcDir)
        cloneDir = os.path.basename(self._srcDir)
        self._run("clone", "--quiet", remoteUrl, cloneDir, cwd=parentDir)
        self._ensureUserInfoIsSet()

    def fetch(self):
        self._run("fetch", "--quiet")

    def merge(self):
        # Force a high rename-threshold: we are not interested in finding renames
        try:
            self._run("merge", "--quiet", "--strategy", "recursive",
                               "--strategy-option", "rename-threshold=100%",
                               "--no-commit", "origin/master")
            return True
        except GitSubprocessError as exc:
            if exc.returncode == 1:
                # Merge failed because of conflicts
                return False
            raise

    def push(self):
        try:
            self._run("push", "--quiet", "origin", "master:master")
        except GitSubprocessError as exc:
            if exc.returncode == 1:
                raise NotFastForwardError() from exc
            else:
                raise

    def hasConflicts(self):
        for status, path in self._getStatus():
            if status in CONFLICT_STATES:
                return True
        return False

    def getConflicts(self):
        for status, path in self._getStatus():
            if status in CONFLICT_STATES:
                if status == "AA":
                    ancestor = None
                else:
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

    def closeConflict(self, path, content):
        fullPath = os.path.join(self._srcDir, path)
        if content is None:
            self._run("rm", "-f", path)
        else:
            with open(fullPath, "wb") as fp:
                fp.write(content)
            self._run("add", path)

    def resetTo(self, commitId):
        self._run("reset", "--hard", commitId)

    def getChangesSince(self, commitId):
        output = self._run("diff", "--name-status", commitId + "..").decode("utf-8")
        return _parseStatusOutput(output)

    def isUpToDate(self):
        output = self._run("branch", "--contains", "origin/master").decode("utf-8")
        for line in output.splitlines():
            if line == '* master':
                return True
        return False

    def getWorkTreeChanges(self):
        output = self._run("status", "-s").decode("utf-8")
        return _parseStatusOutput(output)

    def updateBranch(self, branchName, commitId):
        self._run("branch", "--force", branchName, commitId)

    def getFileContentAt(self, filePath, commitId):
        return self._run("show", commitId + ":" + filePath)

    def getTrackedFiles(self):
        return [x for x in self._run("ls-files").decode("utf-8").split("\n") if x]

    def createTag(self, tag):
        self._run("tag", tag)

    def deleteTag(self, tag):
        self._run("tag", "--delete", tag)

    def hasTag(self, tag):
        # We want this to be very fast, so we avoid forking a git process
        tagPath = os.path.join(self._srcDir, ".git", "refs", "tags", tag)
        return os.path.exists(tagPath)

    def _run(self, *args, **kwargs):
        cwd = kwargs.get("cwd", self._srcDir)
        cmd = ["git", "-C", cwd]
        cmd.extend(args)
        try:
            return subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            raise GitSubprocessError(exc) from exc

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
        except GitSubprocessError as exc:
            if exc.returncode == 1:
                # Key does not exist
                return None
            raise

    def _setConfig(self, section, key, value):
        self._run("config", section + "." + key, value)

    def _getStatus(self):
        output = self._run("status", "--porcelain").decode("utf-8")
        for line in output.splitlines():
            status = line[:2]
            path = line[3:].strip()
            yield status, path
