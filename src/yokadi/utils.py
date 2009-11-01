# coding:utf-8
"""
Common utils functions that cannot fit into dateutils, dbutils or parseutils.
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import os

def shareDirPath():
    """@return: yokadi share dir path"""
    sharePath = ""
    try:
        #TODO: handle windows case
        if os.path.join("src", "yokadi") in __file__:
            # We are in a source tree, look at source root
            sharePath = os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)
        else:
            # We are in a standard Yokadi installation or called by a symlink
            paths=[os.path.dirname(__file__), # Current dir
                   "/usr/share/yokadi",
                   "/usr/local/share/yokadi",
                   "/usr/local/yokadi/share/yokadi",
                   "/opt/yokadi/share/yokadi"]
            for path in paths:
                if os.path.exists(os.path.join(path, "version")):
                    sharePath = path
                    break
    except Exception, e:
        print "Unable to find Yokadi share path"
        print e
        return ""
    return sharePath


def currentVersion():
    """@return: current yokadi version according to 'version' file"""
    try:
        return file(os.path.join(shareDirPath(), "version")).readline().strip("\n")
    except Exception, e:
        print "Unable to read 'version' file. Do you remove or change it ?"
        print e
        return ""
