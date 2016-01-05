import os
import subprocess
import unittest

from os.path import join
from tempfile import TemporaryDirectory

from yokadi.sync.gitvcsimpl import GitVcsImpl


def createGitRepository(path):
    os.mkdir(path)
    subprocess.check_call(('git', 'init', '--quiet'), cwd=path)


def gitAdd(path):
    dirname = os.path.dirname(path)
    basename = os.path.basename(path)
    subprocess.check_call(('git', 'add', basename), cwd=dirname)


def touch(dirname, name):
    path = join(dirname, name)
    open(path, "w").close()
    return path


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

    def testInit(self):
        with TemporaryDirectory() as tmpDir:
            repoDir = join(tmpDir, "repo")
            os.mkdir(repoDir)

            impl = GitVcsImpl()
            impl.setDir(repoDir)
            impl.init()

            gitDir = join(repoDir, ".git")
            self.assertTrue(os.path.exists(gitDir))

    def testIsWorkTreeClean(self):
        with TemporaryDirectory() as tmpDir:
            repoDir = join(tmpDir, "repo")
            createGitRepository(repoDir)

            impl = GitVcsImpl()
            impl.setDir(repoDir)

            self.assertTrue(impl.isWorkTreeClean())

            touch(repoDir, "foo")
            self.assertFalse(impl.isWorkTreeClean())

    def testCommitAll(self):
        with TemporaryDirectory() as tmpDir:
            repoDir = join(tmpDir, "repo")
            createGitRepository(repoDir)
            touch(repoDir, "foo")

            impl = GitVcsImpl()
            impl.setDir(repoDir)

            self.assertFalse(impl.isWorkTreeClean())
            impl.commitAll()
            self.assertTrue(impl.isWorkTreeClean())

    def testClone(self):
        with TemporaryDirectory() as tmpDir:
            remoteRepoDir = join(tmpDir, "remote")
            createGitRepository(remoteRepoDir)

            touch(remoteRepoDir, "foo")
            impl = GitVcsImpl()
            impl.setDir(remoteRepoDir)
            impl.commitAll()

            repoDir = join(tmpDir, "repo")
            impl = GitVcsImpl()
            impl.setDir(repoDir)
            impl.clone(remoteRepoDir)

            fooPath = join(repoDir, "foo")
            self.assertTrue(os.path.exists(fooPath))

    def testGetStatus(self):
        with TemporaryDirectory() as tmpDir:
            repoDir = join(tmpDir, "repo")
            createGitRepository(repoDir)
            impl = GitVcsImpl()
            impl.setDir(repoDir)

            removed = touch(repoDir, "removed")
            impl.commitAll()

            touch(repoDir, "unknown")

            added = touch(repoDir, "added")
            gitAdd(added)

            os.unlink(removed)

            status = set(impl.getStatus())

            self.assertTrue((b' D', b'removed') in status)
            self.assertTrue((b'??', b'unknown') in status)
            self.assertTrue((b'A ', b'added') in status)
            self.assertEqual(len(status), 3)
