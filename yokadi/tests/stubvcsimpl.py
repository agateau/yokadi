"""
Stub version of VcsImpl

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from yokadi.sync import VERSION, VERSION_FILENAME
from yokadi.sync.vcschanges import VcsChanges
from yokadi.sync.vcsimpl import VcsImpl
from yokadi.sync.vcsimplerrors import VcsImplError


class StubVcsImpl(VcsImpl):
    def __init__(self, srcDir="somedir"):
        self._tags = set()
        self._srcDir = srcDir

    @property
    def srcDir(self):
        return self._srcDir

    def isValidVcsDir(self):
        return True

    def init(self):
        pass

    def fetch(self):
        pass

    def merge(self):
        pass

    def hasConflicts(self):
        return bool(self.getConflicts())

    def getConflicts(self):
        return []

    def isWorkTreeClean(self):
        return True

    def closeConflict(self, path, content):
        pass

    def commitAll(self, message=None):
        pass

    def getChangesSince(self, commitId):
        return VcsChanges()

    def getWorkTreeChanges(self):
        return VcsChanges()

    def updateBranch(self, branch, commitId):
        pass

    def getFileContentAt(self, filePath, commitId):
        if filePath == VERSION_FILENAME and commitId == "origin/master":
            return str(VERSION)
        else:
            return "lorem ipsum"

    def hasTag(self, tag):
        return tag in self._tags

    def createTag(self, tag):
        if tag in self._tags:
            raise VcsImplError("tag {} already exists".format(tag))
        self._tags.add(tag)

    def deleteTag(self, tag):
        try:
            self._tags.remove(tag)
        except KeyError:
            raise VcsImplError("tag {} does not exist".format(tag))
