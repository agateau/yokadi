class VcsChanges(object):
    def __init__(self):
        self.added = set()
        self.modified = set()
        self.removed = set()

    def hasChanges(self):
        return bool(self.added) or bool(self.modified) or bool(self.removed)

    def __repr__(self):  # pragma: no cover
        return "<a={} m={} r={}>".format(self.added, self.modified, self.removed)
