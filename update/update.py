#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
This script updates a Yokadi database to the latest version

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or newer
"""

import os
from os.path import abspath, dirname, join
import subprocess
import sys
import shutil
from optparse import OptionParser

from sqlobject import *

import dump

sys.path.append(join(dirname(__file__),"..", "src"))
import yokadi.db

def getVersion(fileName):
    cx = connectionForURI('sqlite:' + fileName)
    if not cx.tableExists("config"):
        return 1
    row = cx.queryOne("select value from config where name='DB_VERSION'")
    return int(row[0])


def setVersion(fileName, version):
    cx = connectionForURI('sqlite:' + fileName)
    assert cx.tableExists("config")
    cx.query("update config set value=%d where name='DB_VERSION'" % version)


def createWorkDb(fileName):
    name = os.path.join(os.path.dirname(fileName), "work.db")
    shutil.copy(fileName, name)
    return name


def createFinalDb(workFileName, finalFileName):
    dumpFileName = "dump.sql"
    print "Dumping into %s" % dumpFileName
    dumpFile = file(dumpFileName, "w")
    dump.dumpDatabase(workFileName, dumpFile)
    dumpFile.close()

    print "Restoring dump from %s into %s" % (dumpFileName, finalFileName)
    sqlhub.processConnection = connectionForURI("sqlite:" + finalFileName)
    yokadi.db.createTables()
    err = subprocess.call(["sqlite3", finalFileName, ".read %s" % dumpFileName])
    if err != 0:
        raise Exception("Dump restoration failed")


def main():
    # Parse args
    parser = OptionParser()

    parser.usage = "%prog <path/to/current.db> <path/to/updated.db>"
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("Wrong argument count")

    dbFileName    = abspath(args[0])
    newDbFileName = abspath(args[1])
    if not os.path.exists(dbFileName):
        parser.error("'%s' does not exist" % dbFileName)

    if os.path.exists(newDbFileName):
        parser.error("'%s' already exists" % newDbFileName)

    # Check version
    version = getVersion(dbFileName)
    print "Found version %d" % version
    if version == yokadi.db.DB_VERSION:
        print "Nothing to do"
        return 0

    # Start import
    workDbFileName = createWorkDb(dbFileName)

    scriptDir = os.path.dirname(__file__) or "."
    oldVersion = getVersion(workDbFileName)
    for version in range(oldVersion, yokadi.db.DB_VERSION):
        scriptFileName = join(scriptDir, "update%dto%d" % (version, version + 1))
        print "Running %s" % scriptFileName
        err = subprocess.call([scriptFileName, workDbFileName])
        if err != 0:
            print "Update failed."
            return 2
    setVersion(workDbFileName, yokadi.db.DB_VERSION)

    createFinalDb(workDbFileName, newDbFileName)

    return 0


if __name__ == "__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
