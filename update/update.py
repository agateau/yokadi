#!/usr/bin/env python
import os
import subprocess
import sys
import shutil
from optparse import OptionParser

from sqlobject import connectionForURI

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
    err = subprocess.call(["/usr/bin/python", "dump.py", workFileName, dumpFileName])
    if err != 0:
        raise Exception("dump.py failed")

    print "Restoring dump from %s into %s" % (dumpFileName, finalFileName)
    err = subprocess.call(["/usr/bin/python", "restore.py", finalFileName,
    dumpFileName])
    if err != 0:
        raise Exception("restore.py failed")


def main():
    parser = OptionParser()

    parser.add_option("-d", "--db", dest="fileName",
                      help="TODO database", metavar="FILE")

    (options, args) = parser.parse_args()

    if not options.fileName:
        print "You must provide a database with --db option"
        sys.exit(1)

    dbFileName = os.path.abspath(options.fileName)

    version = getVersion(dbFileName)
    print "Found version %d" % version
    if version == CURRENT_DB_VERSION:
        print "Nothing to do"
        return 0

    newDbFileName = dbFileName + "-v%d" % CURRENT_DB_VERSION
    if os.path.exists(newDbFileName):
        print "Output database file (%s) already exists" % newDbFileName
        return 1

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
