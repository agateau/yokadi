#!/usr/bin/env python
import os
import subprocess
import sys
import shutil
from optparse import OptionParser

from sqlobject import connectionForURI

import dump
import update1to2

CURRENT_DB_VERSION = 2

def getVersion(fileName):
    cx = connectionForURI('sqlite:' + fileName)
    if not cx.tableExists("config"):
        return 1
    row = cx.queryOne("select value from config where name='DB_VERSION'")
    return int(row[0])


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
    err = subprocess.call(["/usr/bin/python", "restore.py", finalFileName,
    dumpFileName])
    if err != 0:
        raise Exception("restore.py failed")


def main():
    # Parse args
    parser = OptionParser()

    parser.usage = "%prog <path/to/old.db> <path/to/updated.db>"
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("Wrong argument count")

    dbFileName = args[0]
    newDbFileName = args[1]
    if not os.path.exists(dbFileName):
        parser.error("'%s' does not exist" % dbFileName)

    if os.path.exists(newDbFileName):
        parser.error("'%s' already exists" % newDbFileName)

    dbFileName = os.path.abspath(dbFileName)

    # Check version
    version = getVersion(dbFileName)
    print "Found version %d" % version
    if version == CURRENT_DB_VERSION:
        print "Nothing to do"
        return 0

    # Start import
    workDbFileName = createWorkDb(dbFileName)

    while True:
        version = getVersion(workDbFileName)
        if version == CURRENT_DB_VERSION:
            break
        mod = eval("update%dto%d" % (version, version + 1))
        mod.updateDb(workDbFileName)
        print "Updated to version %d" % (version + 1)

    createFinalDb(workDbFileName, newDbFileName)

    return 0


if __name__ == "__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
