"""
Stub version of PullUi

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from yokadi.sync.pullui import PullUi


class StubPullUi(PullUi):
    def __init__(self):
        self.renames = []

    def resolveConflicts(self, conflictingObjects):
        pass

    def addRename(self, domain, old, new):
        self.renames.append((domain, old, new))

    def reportProgress(self, message):
        pass

    def reportError(self, message):
        pass
