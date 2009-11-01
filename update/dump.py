#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Generates a data-only sqlite dump, with insert statements including column
names.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or newer
"""

import os
import re
import subprocess
import sys
try:
    # Seems to be the Python 2.6 way to get sqlite
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite


def getTableList(cx):
    cursor = cx.cursor()
    cursor.execute("select name from sqlite_master where type='table'")
    return [x[0] for x in cursor.fetchall()]


def getTableColumnList(cx, table):
    cursor = cx.cursor()
    cursor.execute("select * from %s" % table)
    return [x[0] for x in cursor.description]


def dumpTable(cx, dbFileName, table, fl):
    rx = re.compile(u"^insert into %s values" % table, re.IGNORECASE)

    columnList = getTableColumnList(cx, table)
    newText = u"insert into %s(%s) values" % (table, ",".join(columnList))

    child = subprocess.Popen(["sqlite3", dbFileName], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    child.stdin.write(".mode insert %s\nselect * from %s;\n" % (table, table))
    child.stdin.close()

    for line in child.stdout.readlines():
        line = unicode(line, "utf-8")
        line = rx.sub(newText, line)
        fl.write(line.encode("utf-8"))


def dumpDatabase(dbFileName, dumpFile):
    cx = sqlite.connect(os.path.abspath(dbFileName))
    for table in getTableList(cx):
        dumpTable(cx, dbFileName, table, dumpFile)


def main():
    dbFileName = sys.argv[1]
    dumpFileName = sys.argv[2]
    dumpFile = file(dumpFileName, "w")
    dumpDatabase(dbFileName, dumpFile)


if __name__ == "__main__":
    main()
# vi: ts=4 sw=4 et
