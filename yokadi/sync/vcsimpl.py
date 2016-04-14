class VcsImpl(object):
    """
    An abstract class representing a VCS
    """
    def setDir(self, srcDir):
        """
        Defines the directory of the VCS work tree
        """
        raise NotImplementedError()

    def isValidVcsDir(self):
        """
        Returns True if the dir set with setDir is a valid VCS work tree
        """
        raise NotImplementedError()

    def init(self):
        """
        Initialize a repository in the work tree dir
        """
        raise NotImplementedError()

    def isWorkTreeClean(self):
        """
        Returns True if the work tree contains no unsaved changes
        """
        raise NotImplementedError()

    def commitAll(self, message=None):
        """
        Commit all changes, using `message` as a commit message
        """
        raise NotImplementedError()

    def clone(self, remoteUrl):
        """
        Create a clone of `remoteUrl` in the dir defined with `setDir`
        """
        raise NotImplementedError()

    def pull(self):
        """
        Pull changes from the remote repository.
        Returns True on success, False in case of conflicts.
        """
        raise NotImplementedError()

    def hasConflicts(self):
        """
        Returns True if there are conflicts in the work tree
        """
        raise NotImplementedError()

    def getConflicts(self):
        """
        Returns a list of VcsConflict instances for conflicting paths
        """
        raise NotImplementedError()

    def closeConflict(self, path, content):
        """
        Solves the conflict
        If `content` is empty delete path. If `content` is not empty writes
        content to path.
        `content` must be of type `bytes`.
        """
        raise NotImplementedError()

    def abortMerge(self):
        """
        Should be called after a pull which failed with conflicts, to abort
        changes
        """
        raise NotImplementedError()

    def getChangesSince(self, commitId):
        """
        Returns an instance of VcsChanges listing all changes since `commitId`
        """
        raise NotImplementedError()

    def updateBranch(self, branchName, commitId):
        """
        Makes the branch `branchName` point to `commitId`
        """
        raise NotImplementedError()

    def getFileContentAt(self, filePath, commitId):
        """
        Returns the content of `filePath` at `commitId` as bytes
        """
        raise NotImplementedError()

    def getTrackedFiles(self):
        """
        Returns a list of all tracked files
        """
        raise NotImplementedError()
