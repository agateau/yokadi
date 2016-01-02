"""
Various file utility functions

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os


def createParentDirs(path, mode=0o777):
    parent = os.path.dirname(path)
    if os.path.exists(parent):
        return
    os.makedirs(parent, mode=mode)
