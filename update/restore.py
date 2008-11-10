#!/usr/bin/env python
import os
import sys
import subprocess

from sqlobject import *

sys.path.append("..")
import db

def main():
    dbFileName = os.path.abspath(sys.argv[1])
    dumpFileName = sys.argv[2]

    # Create database
    sqlhub.processConnection = connectionForURI("sqlite:" + dbFileName)
    db.createTables()

    return subprocess.call(["sqlite3", dbFileName, ".read %s" % dumpFileName])


if __name__ == "__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
