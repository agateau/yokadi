import os
import subprocess


class GitVcsImpl(object):
    name = "Git"

    def setDir(self, srcDir):
        self._srcDir = srcDir

    def isValidVcsDir(self):
        gitDir = os.path.join(self._srcDir, ".git")
        return os.path.exists(gitDir)

    def init(self):
        self._run("init")

    def isWorkTreeClean(self):
        return len(list(self.getStatus())) == 0

    def commit(self, message=None):
        if message is None:
            message = "Synced"
        self._run("add", ".")
        self._run("commit", "-m", message)

    def pull(self):
        # Force a high rename-threshold: we are not interested in finding renames
        self._run("pull", "--strategy", "recursive",
                          "--strategy-option", "rename-threshold=100%")

    def getConflicts(self):
        """
        Returns a list of (status, path) for conflicting paths:

        <status> is a two letter string which can take the following values:

           D           D    unmerged, both deleted
           A           U    unmerged, added by us
           U           D    unmerged, deleted by them
           U           A    unmerged, added by them
           D           U    unmerged, deleted by us
           A           A    unmerged, both added
           U           U    unmerged, both modified
        """
        CONFLICTS = set(["DD", "AU", "UD", "UA", "DU", "AA", "UU"])

        for status, path in self.getStatus():
            if status in CONFLICTS:
                yield status, path

    def abortMerge(self):
        self._run("merge", "--abort")

    def _run(self, *args):
        cmd = ["git", "-C", self._srcDir]
        cmd.extend(args)
        return subprocess.check_output(cmd)

    def getStatus(self):
        output = self._run("status", "--porcelain")
        for line in output.splitlines():
            status = line[:2]
            path = line[3:].strip()
            yield status, path
