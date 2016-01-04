import os
import subprocess
import unittest

from os.path import join
from tempfile import TemporaryDirectory

from yokadi.sync.gitvcsimpl import GitVcsImpl

def createGitRepository(path):
    os.mkdir(path)
    subprocess.check_call(('git', 'init', '--quiet'), cwd=path)


class GitVcsImplTestCase(unittest.TestCase):
    def testIsValidVcsDir(self):
        with TemporaryDirectory() as tmpDir:
            repoDir = join(tmpDir, "repo")
            createGitRepository(repoDir)
            impl = GitVcsImpl()

            impl.setDir(repoDir)
            self.assertTrue(impl.isValidVcsDir())

            impl.setDir(tmpDir)
            self.assertFalse(impl.isValidVcsDir())
