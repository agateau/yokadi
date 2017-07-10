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
import shutil
import tempfile

from yokadi.core import fileutils


_WINDOWS = os.name == "nt"

DB_NAME = "yokadi.db"


class MigrationException(Exception):
    pass


def _getAppDataDir():
    assert _WINDOWS
    return os.environ["APPDATA"]


def getRuntimeDir():
    value = os.getenv("XDG_RUNTIME_DIR")
    if not value:
        # Running on a system where XDG_RUNTIME_DIR is not set, fallback to
        # $tempdir/yokadi-$user
        tmpdir = tempfile.gettempdir()
        value = os.path.join(tmpdir, "yokadi-" + getpass.getuser())
    return value


def getLogDir():
    return getCacheDir()


def getCacheDir():
    if _WINDOWS:
        value = os.path.join(_getAppDataDir(), "yokadi", "cache")
    else:
        cacheBaseDir = os.getenv("XDG_CACHE_HOME")
        if not cacheBaseDir:
            cacheBaseDir = os.path.expandvars("$HOME/.cache")
        value = os.path.join(cacheBaseDir, "yokadi")
    return value


def getDataDir():
    xdgDataDir = os.environ.get("XDG_DATA_HOME")
    if xdgDataDir:
        return os.path.join(xdgDataDir, "yokadi")

    if _WINDOWS:
        return os.path.join(_getAppDataDir(), "yokadi", "data")

    return os.path.expandvars("$HOME/.local/share/yokadi")


def getHistoryPath():
    path = os.getenv("YOKADI_HISTORY")
    if path:
        return path
    return os.path.join(getCacheDir(), "history")


def getDbPath(dataDir):
    path = os.getenv("YOKADI_DB")
    if path:
        return path
    return os.path.join(dataDir, "yokadi.db")


def _getOldHistoryPath():
    if _WINDOWS:
        return os.path.join(_getAppDataDir(), ".yokadi_history")
    else:
        return os.path.expandvars("$HOME/.yokadi_history")


def migrateOldHistory():
    oldHistoryPath = _getOldHistoryPath()
    if not os.path.exists(oldHistoryPath):
        return

    newHistoryPath = getHistoryPath()
    if os.path.exists(newHistoryPath):
        # History is not critical, just overwrite the new file
        os.unlink(newHistoryPath)
    fileutils.createParentDirs(newHistoryPath)
    shutil.move(oldHistoryPath, newHistoryPath)
    print("Moved %s to %s" % (oldHistoryPath, newHistoryPath))


def migrateOldDb(newDbPath):
    oldDbPath = os.path.normcase(os.path.expandvars("$HOME/.yokadi.db"))
    if not os.path.exists(oldDbPath):
        return

    if os.path.exists(newDbPath):
        raise MigrationException("Tried to move %s to %s, but %s already exists."
                                 " You must remove one of the two files." % (oldDbPath, newDbPath, newDbPath))
    fileutils.createParentDirs(newDbPath)
    shutil.move(oldDbPath, newDbPath)
    print("Moved %s to %s" % (oldDbPath, newDbPath))
