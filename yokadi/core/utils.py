# coding:utf-8
"""
Common utils functions that cannot fit into ydateutils, dbutils or parseutils.
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import os


def shareDirPath():
    """@return: yokadi share dir path"""
    # TODO: handle windows case
    if os.path.join("src", "yokadi") in __file__:
        # We are in a source tree, look at source root
        return os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, os.path.pardir)

    # We are in a standard Yokadi installation or called by a symlink
    paths = [os.path.dirname(__file__),  # Current dir
           "/usr/share/yokadi",
           "/usr/local/share/yokadi",
           "/usr/local/yokadi/share/yokadi",
           "/opt/yokadi/share/yokadi"]
    for path in paths:
        if os.path.exists(path):
            return path
    print("Unable to find Yokadi share path")
    return ""
