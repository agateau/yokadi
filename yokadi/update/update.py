#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
This script updates a Yokadi database to the latest version

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""

import os
import shutil
import sqlite3
import sys
import time
from argparse import ArgumentParser
from tempfile import TemporaryDirectory

from yokadi.core import basepaths
from yokadi.core import db
from yokadi.sync import VERSION as DUMP_VERSION
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync.dump import readVersionFile, createVersionFile
from yokadi.sync.syncmanager import SyncManager

from yokadi.update import updateutils

# Those modules look unused, but they are used "dynamically"
from yokadi.update import update1to2  # noqa
from yokadi.update import update2to3  # noqa
from yokadi.update import update3to4  # noqa
from yokadi.update import update4to5  # noqa
from yokadi.update import update5to6  # noqa
from yokadi.update import update6to7  # noqa
from yokadi.update import update7to8  # noqa
from yokadi.update import update8to9  # noqa
from yokadi.update import update9to10  # noqa
from yokadi.update import update10to11  # noqa
from yokadi.update import update11to12  # noqa


BEFORE_UPDATE_TAG = 'before-update'


def err(message):
    print("error: " + message, file=sys.stderr)


def getVersion(fileName):
    database = db.Database(fileName, createIfNeeded=False, updateMode=True)
    return database.getVersion()


def setVersion(fileName, version):
    database = db.Database(fileName, createIfNeeded=False, updateMode=True)
    database.setVersion(version)


def importTable(dstCursor, srcCursor, table):
    columns = updateutils.getTableColumnList(dstCursor, table)
    columnString = ", ".join(columns)
    sql = "select {} from {}".format(columnString, table)

    placeHolders = ", ".join(["?"] * len(columns))
    insertSql = "insert into {}({}) values({})".format(table, columnString, placeHolders)

    query = srcCursor.execute(sql)
    while True:
        rows = query.fetchmany(size=100)
        if not rows:
            break
        dstCursor.executemany(insertSql, rows)


def updateSyncDump(dbPath, dumpDir):
    currentDumpVersion = readVersionFile(dumpDir)
    if currentDumpVersion == DUMP_VERSION:
        print('Sync dump does not need to be recreated')
        return
    assert currentDumpVersion < DUMP_VERSION, \
        'current dump version is greater than the target dump. This should not happen!'

    db.connectDatabase(dbPath)

    print('Recreating sync dump')
    vcsImpl = GitVcsImpl(dumpDir)
    syncManager = SyncManager(session=db.getSession(), vcsImpl=vcsImpl)
    vcsImpl.createTag(BEFORE_UPDATE_TAG)
    try:
        createVersionFile(dumpDir)
        syncManager.clearDump()
        syncManager.dump()
    except:
        err('An exception has occurred while recreating dump. Resetting dump.')
        vcsImpl.resetTo(BEFORE_UPDATE_TAG)
        raise
    finally:
        vcsImpl.deleteTag(BEFORE_UPDATE_TAG)


def recreateDb(workPath, destPath):
    assert os.path.exists(workPath)

    print("Recreating the database")
    database = db.Database(destPath, createIfNeeded=True, updateMode=True)  # noqa

    print("Importing content to the new database")
    srcConn = sqlite3.connect(workPath)
    srcCursor = srcConn.cursor()
    dstConn = sqlite3.connect(destPath)
    dstCursor = dstConn.cursor()

    for table in updateutils.getTableList(dstCursor):
        importTable(dstCursor, srcCursor, table)
    dstConn.commit()


def update(dataDir, newDataDir=None, inplace=True):
    # Check paths
    dbPath = os.path.join(dataDir, basepaths.DB_NAME)
    if not os.path.exists(dbPath):
        err("'{}' does not exist.".format(dbPath))
        return 1

    if not inplace:
        if os.path.exists(newDataDir):
            err("'{}' already exists.".format(newDataDir))
            return 1
        else:
            os.mkdir(newDataDir)

    # Check version
    version = getVersion(dbPath)
    print("Found version %d" % version)

    if version == db.DB_VERSION:
        print("Nothing to do")
        return 0

    if inplace:
        destDir = dataDir
    else:
        destDir = newDataDir
    with TemporaryDirectory(prefix="yokadi-update-", dir=destDir) as tempDir:
        # Copy the DB
        workDbPath = os.path.join(tempDir, "work.db")
        shutil.copy(dbPath, workDbPath)

        # Start import
        oldVersion = getVersion(workDbPath)

        with sqlite3.connect(workDbPath) as conn:
            cursor = conn.cursor()

            for version in range(oldVersion, db.DB_VERSION):
                moduleName = "update{}to{}".format(version, version + 1)
                print("Updating to {}".format(version + 1))
                module = globals()[moduleName]
                module.update(cursor)

        setVersion(workDbPath, db.DB_VERSION)

        # Recreate the DB
        recreatedDbPath = os.path.join(tempDir, "recreated.db")
        recreateDb(workDbPath, recreatedDbPath)

        # Move to final paths
        if inplace:
            base, ext = os.path.splitext(dbPath)
            timestamp = time.strftime("%Y%m%d")
            backupPath = base + "-v{}-{}".format(oldVersion, timestamp) + ext
            os.rename(dbPath, backupPath)
            print("Old database renamed to {}".format(backupPath))
            os.rename(recreatedDbPath, dbPath)
        else:
            newDbPath = basepaths.getDbPath(newDataDir)
            os.rename(recreatedDbPath, newDbPath)

    # Update sync dump if required
    dumpDir = basepaths.getSyncDumpDir(dataDir)
    if os.path.exists(dumpDir):
        if inplace:
            updateSyncDump(dbPath, dumpDir)
        else:
            newDumpDir = basepaths.getSyncDumpDir(newDataDir)
            shutil.copytree(dumpDir, newDumpDir)
            updateSyncDump(newDbPath, newDumpDir)

    return 0


def main():
    # Parse args
    parser = ArgumentParser()
    parser.add_argument('--datadir', metavar='<path/to/current/datadir>',
                        help="Path to the datadir to update.")
    parser.add_argument('--updated-datadir', dest='updated', metavar='<path/to/updated/datadir>',
                        help="Path to the destination datadir. Mandatory unless --in-place is used",
                        nargs="?")
    parser.add_argument("-i", "--in-place",
                        dest="inplace", action="store_true",
                        help="Replace current file")

    args = parser.parse_args()

    dataDir = os.path.abspath(args.datadir)

    if args.inplace:
        newDataDir = None
        if args.updated:
            parser.error('Cannot use --updated or with --in-place')
    else:
        newDataDir = os.path.abspath(args.updated)

    return update(dataDir, newDataDir, inplace=args.inplace)


if __name__ == "__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
