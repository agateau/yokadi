class PullUi(object):
    MERGE = "merge"
    RENAME = "rename"
    CANCEL = "cancel"

    def resolveConflicts(self, conflictingObjects):
        """
        Must iterate on all conflicting objects and resolve them
        """
        raise NotImplementedError()

    def getMergeStrategy(self, localProjectDict, remoteProjectDict):
        """
        Must return either MERGE, RENAME or CANCEL
        """
        raise NotImplementedError()
