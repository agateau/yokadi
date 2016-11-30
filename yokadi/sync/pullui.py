"""
"User interface" for functions of the `pull` module

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""


class PullUi(object):
    def resolveConflicts(self, conflictingObjects):
        """
        Must iterate on all conflicting objects and resolve them
        """
        raise NotImplementedError()

    def addRename(self, domain, old, new):
        """
        Called when an object is renamed. Should store the information to
        display it at the end of the pull.

        @param domain The object domain
        @param old The old name
        @param new The new name
        """
        raise NotImplementedError()
