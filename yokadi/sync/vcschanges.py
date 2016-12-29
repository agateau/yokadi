"""
Represents changes recorded by a VCS.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""


class VcsChanges(object):
    def __init__(self, added=None, modified=None, removed=None):
        self.added = added or set()
        self.modified = modified or set()
        self.removed = removed or set()

    def hasChanges(self):
        return bool(self.added) or bool(self.modified) or bool(self.removed)

    def __eq__(self, other):
        return self.added == other.added and self.modified == other.modified and self.removed == other.removed

    def __repr__(self):  # pragma: no cover
        return "<a={} m={} r={}>".format(self.added, self.modified, self.removed)

    def update(self, other):
        self.added.difference_update(other.removed)
        self.modified.difference_update(other.removed)
        self.removed.difference_update(other.added)

        self.added.update(other.added)
        self.modified.update(other.modified)
        self.removed.update(other.removed)
