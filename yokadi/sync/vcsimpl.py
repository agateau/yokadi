"""
Base class for VCS implementations used by the synchronization code

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""


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
        Commit all changes, using `message` as a commit message. Must raise
        CantCommitWithConflictsError if there are conflicts in the work tree.
        """
        raise NotImplementedError()

    def clone(self, remoteUrl):
        """
        Create a clone of `remoteUrl` in the dir defined with `setDir`
        """
        raise NotImplementedError()

    def fetch(self):
        """
        Download changes from the remote repository. Must *not* apply them to
        the local copy.
        """
        raise NotImplementedError()

    def merge(self):
        """
        Merge remote branch with local branch. Must *not* commit changes.
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

    def resetTo(self, commitId):
        """
        Resets current branch to `commitId`
        """
        raise NotImplementedError()

    def getWorkTreeChanges(self):
        """
        Returns an instance of VcsChanges listing all uncommitted changes

        Considers unknown files as if they had been added because they would be
        added by a call to commitAll().
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

    def hasTag(self, tag):
        """
        Returns True if `tag` exists
        """
        raise NotImplementedError()

    def createTag(self, tag):
        """
        Creates the tag `tag`. Raises VcsImplError if the tag already exists
        """
        raise NotImplementedError()

    def deleteTag(self, tag):
        """
        Deletes the tag `tag`. Raises VcsImplError if the tag does not exist
        """
        raise NotImplementedError()
