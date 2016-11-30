"""
A POD to store information about a conflict

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from collections import namedtuple


VcsConflict = namedtuple("VcsConflict", ["path", "ancestor", "local", "remote"])
