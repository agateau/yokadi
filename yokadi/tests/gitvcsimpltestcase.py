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


def createBranch(repoDir, name):
    subprocess.check_call(('git', 'branch', name), cwd=repoDir)


def getBranchCommitId(repoDir, name="master"):
    path = os.path.join(repoDir, ".git", "refs", "heads", name)
    with open(path) as f:
        return f.read().strip()


def touch(dirname, name):
    path = join(dirname, name)
    open(path, "w").close()
    return path


def createGitRepositoryWithConflict(tmpDir, path, localContent="", remoteContent=""):
    """
    @param localContent is the content of the local file, use None to remove it
    @param remoteContent is the content of the remote file, use None to remove it
    """
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
    if remoteContent is None:
        os.unlink(remoteFooPath)
    else:
        with open(remoteFooPath, "w") as f:
            f.write(remoteContent)
    remoteImpl.commitAll()

    # Modify local
    fooPath = join(repoDir, "foo")
    if localContent is None:
        os.unlink(fooPath)
    else:
        with open(fooPath, "w") as f:
            f.write(localContent)
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
        with TemporaryDirectory() as tmpDir:
            remoteRepoDir = join(tmpDir, "remote")
            createGitRepository(remoteRepoDir)

            touch(remoteRepoDir, "foo")
            impl = GitVcsImpl()
            impl.setDir(remoteRepoDir)
            impl.commitAll()

            self._deleteGitConfig()

            repoDir = join(tmpDir, "repo")
            impl = GitVcsImpl()
            impl.setDir(repoDir)
            impl.clone(remoteRepoDir)

            touch(repoDir, "bar")
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
            impl = createGitRepositoryWithConflict(tmpDir, "repo",
                    localContent="local",
                    remoteContent="remote")

            conflicts = list(impl.getConflicts())
            self.assertEqual(len(conflicts), 1)
            conflict = conflicts[0]
            self.assertEqual(conflict.path, "foo")
            self.assertEqual(conflict.ancestor, b"")
            self.assertEqual(conflict.local, b"local")
            self.assertEqual(conflict.remote, b"remote")

    def testGetConflictsRemovedLocally(self):
        with TemporaryDirectory() as tmpDir:
            impl = createGitRepositoryWithConflict(tmpDir, "repo",
                    localContent=None,
                    remoteContent="remote")

            conflicts = list(impl.getConflicts())
            self.assertEqual(len(conflicts), 1)
            conflict = conflicts[0]
            self.assertEqual(conflict.path, "foo")
            self.assertEqual(conflict.ancestor, b"")
            self.assertEqual(conflict.local, None)
            self.assertEqual(conflict.remote, b"remote")

    def testGetConflictsRemovedRemotely(self):
        with TemporaryDirectory() as tmpDir:
            impl = createGitRepositoryWithConflict(tmpDir, "repo",
                    localContent="local",
                    remoteContent=None)

            conflicts = list(impl.getConflicts())
            self.assertEqual(len(conflicts), 1)
            conflict = conflicts[0]
            self.assertEqual(conflict.path, "foo")
            self.assertEqual(conflict.ancestor, b"")
            self.assertEqual(conflict.local, b"local")
            self.assertEqual(conflict.remote, None)

    def testAbortMerge(self):
        with TemporaryDirectory() as tmpDir:
            impl = createGitRepositoryWithConflict(tmpDir, "repo",
                    remoteContent="hello",
                    localContent="world")
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

            self.assertTrue((' D', 'removed') in status)
            self.assertTrue(('??', 'unknown') in status)
            self.assertTrue(('A ', 'added') in status)
            self.assertEqual(len(status), 3)

    def testUpdateBranch(self):
        with TemporaryDirectory() as tmpDir:
            repoDir = join(tmpDir, "repo")
            createGitRepository(repoDir)
            impl = GitVcsImpl()
            impl.setDir(repoDir)

            # Create a foo branch which lags behind master
            touch(repoDir, "file1")
            impl.commitAll()

            createBranch(repoDir, "foo")
            fooId = getBranchCommitId(repoDir, "foo")

            touch(repoDir, "file2")
            impl.commitAll()
            masterId = getBranchCommitId(repoDir, "master")

            self.assertNotEqual(fooId, masterId)

            # Update branch, branch ids should be the same now
            impl.updateBranch("foo", "master")

            fooId = getBranchCommitId(repoDir, "foo")
            self.assertEqual(fooId, masterId)

    def testGetChangesSince(self):
        with TemporaryDirectory() as tmpDir:
            repoDir = join(tmpDir, "repo")
            createGitRepository(repoDir)
            impl = GitVcsImpl()
            impl.setDir(repoDir)

            # Create a repo with a removed, a modified and an added file
            modifiedPath = touch(repoDir, "modified")
            removedPath = touch(repoDir, "removed")
            impl.commitAll()

            # Add a new file
            beforeAddId = getBranchCommitId(repoDir)
            touch(repoDir, "added")
            impl.commitAll()

            changes = impl.getChangesSince(beforeAddId)
            self.assertEqual(changes.modified, set())
            self.assertEqual(changes.added, {"added"})
            self.assertEqual(changes.removed, set())

            # Remove a file
            beforeRemoveId = getBranchCommitId(repoDir)
            os.unlink(removedPath)
            impl.commitAll()

            changes = impl.getChangesSince(beforeRemoveId)
            self.assertEqual(changes.modified, set())
            self.assertEqual(changes.added, set())
            self.assertEqual(changes.removed, {"removed"})

            changes = impl.getChangesSince(beforeAddId)
            self.assertEqual(changes.modified, set())
            self.assertEqual(changes.added, {"added"})
            self.assertEqual(changes.removed, {"removed"})

            # Modify a file
            beforeModifyId = getBranchCommitId(repoDir)
            with open(modifiedPath, "w") as f:
                f.write("Boo")
            impl.commitAll()

            changes = impl.getChangesSince(beforeModifyId)
            self.assertEqual(changes.modified, {"modified"})
            self.assertEqual(changes.added, set())
            self.assertEqual(changes.removed, set())

            changes = impl.getChangesSince(beforeRemoveId)
            self.assertEqual(changes.modified, {"modified"})
            self.assertEqual(changes.added, set())
            self.assertEqual(changes.removed, {"removed"})

            changes = impl.getChangesSince(beforeAddId)
            self.assertEqual(changes.modified, {"modified"})
            self.assertEqual(changes.added, {"added"})
            self.assertEqual(changes.removed, {"removed"})
