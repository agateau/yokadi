import os
import platform
import subprocess

from yokadi.sync.vcschanges import VcsChanges


class GitVcsImpl(object):
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
        return len(list(self.getStatus())) == 0

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
        # Force a high rename-threshold: we are not interested in finding renames
        try:
            self._run("merge", "--quiet", "--strategy", "recursive",
                               "--strategy-option", "rename-threshold=100%",
                               "FETCH_HEAD")
            return True
        except subprocess.CalledProcessError as exc:
            if exc.returncode == 1:
                # Merge failed because of conflicts
                return False
            raise exc

    def getConflicts(self):
        """
        Returns a list of (status, path) for conflicting paths:

        <status> is a two letter string which can take the following values:

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
        Should not happen with guid-based file names.

        AA: unmerged, both added
        Both local and remote created A.
        Should not happen with guid-based file names.
        """
        CONFLICTS = set([b"DD", b"AU", b"UD", b"UA", b"DU", b"AA", b"UU"])

        for status, path in self.getStatus():
            if status in CONFLICTS:
                yield status, path

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
        """
        Make the branch `branchName` point to `commitId`
        """
        self._run("branch", "--force", branchName, commitId)

    def _run(self, *args, **kwargs):
        cwd = kwargs.get("cwd", self._srcDir)
        cmd = ["git", "-C", cwd]
        cmd.extend(args)
        return subprocess.check_output(cmd)

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

    def getStatus(self):
        output = self._run("status", "--porcelain")
        for line in output.splitlines():
            status = line[:2]
            path = line[3:].strip()
            yield status, path
