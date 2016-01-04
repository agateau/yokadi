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
        self.commit("Created")

    def isWorkTreeClean(self):
        out = self._run("status", "-s")
        return len(out) == 0

    def commit(self, message=None):
        if message is None:
            message = "Synced"
        self._run("add", ".")
        self._run("commit", "-m", message)

    def _run(self, *args):
        cmd = ["git", "-C", self._srcDir]
        cmd.extend(args)
        return subprocess.check_output(cmd)
