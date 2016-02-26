from collections import namedtuple


VcsConflict = namedtuple("VcsConflict", ["path", "ancestor", "local", "remote"])
