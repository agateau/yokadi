import os
import shutil
import subprocess
import tempfile
import unittest

from os.path import join
from tempfile import TemporaryDirectory

from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.tests.testutils import EnvironSaver


def createGitRepository(path):
    os.mkdir(path)
    subprocess.check_call(('git', 'init', '--quiet'), cwd=path)


def createGitConfig():
    subprocess.check_call(('git', 'config', '--global', 'user.name', 'Test User'))
    subprocess.check_call(('git', 'config', '--global', 'user.email', 'test@example.com'))


def gitAdd(path):
    dirname = os.path.dirname(path)
    basename = os.path.basename(path)
    subprocess.check_call(('git', 'add', basename), cwd=dirname)


def touch(dirname, name):
    path = join(dirname, name)
    open(path, "w").close()
    return path


def createGitRepositoryWithConflict(tmpDir, path):
    # Create remote repo
    remoteRepoDir = join(tmpDir, path + "-remote")
    createGitRepository(remoteRepoDir)
    remoteImpl = GitVcsImpl()
    remoteImpl.setDir(remoteRepoDir)
    remoteFooPath = touch(remoteRepoDir, "foo")
    remoteImpl.commitAll()

    # Clone it
    repoDir = join(tmpDir,path)
    impl = GitVcsImpl()
    impl.setDir(repoDir)
    impl.clone(remoteRepoDir)

    # Modify remote
    with open(remoteFooPath, "w") as f:
        f.write("hello")
    remoteImpl.commitAll()

    # Modify local
    fooPath = join(repoDir, "foo")
    with open(fooPath, "w") as f:
        f.write("world")
    impl.commitAll()

    # Pull => conflict
    impl.pull()
    return impl


class GitVcsImplTestCase(unittest.TestCase):
    def setUp(self):
        self._envSaver = EnvironSaver()
        self.testHomeDir = tempfile.mkdtemp(prefix="yokadi-basepaths-testcase")
        os.environ["HOME"] = self.testHomeDir
        createGitConfig()

    def tearDown(self):
        shutil.rmtree(self.testHomeDir)
        self._envSaver.restore()

    def _deleteGitConfig(self):
        os.remove(join(self.testHomeDir, ".gitconfig"))

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

    def testInitNoGitUserInfo(self):
        # If there is no user info, init() should set some default info so that
        # commitAll() does not fail
        self._deleteGitConfig()
        with TemporaryDirectory() as tmpDir:
            repoDir = join(tmpDir, "repo")
            os.mkdir(repoDir)

            impl = GitVcsImpl()
            impl.setDir(repoDir)
            impl.init()

            touch(repoDir, "foo")
            impl.commitAll()

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

    def testCloneNoGitUserInfo(self):
        self._deleteGitConfig()
        with TemporaryDirectory() as tmpDir:
            remoteRepoDir = join(tmpDir, "remote")
            createGitRepository(remoteRepoDir)

            touch(remoteRepoDir, "foo")
            impl = GitVcsImpl()
            impl.setDir(remoteRepoDir)
            impl.commitAll()

    def testPull(self):
        with TemporaryDirectory() as tmpDir:
            remoteRepoDir = join(tmpDir, "remote")
            createGitRepository(remoteRepoDir)
            remoteImpl = GitVcsImpl()
            remoteImpl.setDir(remoteRepoDir)
            touch(remoteRepoDir, "bar")
            remoteImpl.commitAll()

            repoDir = join(tmpDir, "repo")
            impl = GitVcsImpl()
            impl.setDir(repoDir)
            impl.clone(remoteRepoDir)

            fooPath = join(repoDir, "foo")
            self.assertFalse(os.path.exists(fooPath))

            touch(remoteRepoDir, "foo")
            remoteImpl.commitAll()

            ok = impl.pull()
            self.assertTrue(ok)
            self.assertTrue(os.path.exists(fooPath))

    def testGetConflicts(self):
        with TemporaryDirectory() as tmpDir:
            impl = createGitRepositoryWithConflict(tmpDir, "repo")

            conflicts = set(impl.getConflicts())
            self.assertTrue((b"UU", b"foo") in conflicts)
            self.assertEqual(len(conflicts), 1)

    def testAbortMerge(self):
        with TemporaryDirectory() as tmpDir:
            impl = createGitRepositoryWithConflict(tmpDir, "repo")
            conflicts = set(impl.getConflicts())
            self.assertEqual(len(conflicts), 1)
            impl.abortMerge()
            conflicts = set(impl.getConflicts())
            self.assertEqual(len(conflicts), 0)

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
