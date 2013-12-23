# -*- coding: UTF-8 -*-
"""
Provide standard ways to get various dirs

This is similar to th pyxdg module but it does not automatically creates the
dirs. Not creating the dirs is important to be able to show default values in
`yokadid --help` output without creating anything.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os
import getpass
import tempfile

# FIXME: We probably want a Windows version of this


def getRuntimeDir():
    value = os.environ.get("XDG_RUNTIME_DIR")
    if value:
        return value

    # Running on a system where XDG_RUNTIME_DIR is not set, fallback to
    # $tempdir/yokadi-$user
    tmpdir = tempfile.gettempdir()
    return os.path.join(tmpdir, "yokadi-" + getpass.getuser())


def getLogDir():
    cacheHome = os.environ.get("XDG_CACHE_HOME")
    if not cacheHome:
        cacheHome = os.path.expanduser("~/.cache")
    return os.path.join(cacheHome, "yokadi")
