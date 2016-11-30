"""
Represents changes recorded by a VCS.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""


class VcsChanges(object):
    def __init__(self):
        self.added = set()
        self.modified = set()
        self.removed = set()

    def hasChanges(self):
        return bool(self.added) or bool(self.modified) or bool(self.removed)

    def __repr__(self):  # pragma: no cover
        return "<a={} m={} r={}>".format(self.added, self.modified, self.removed)

    def update(self, other):
        self.added.difference_update(other.removed)
        self.modified.difference_update(other.removed)
        self.removed.difference_update(other.added)

        self.added.update(other.added)
        self.modified.update(other.modified)
        self.removed.update(other.removed)
