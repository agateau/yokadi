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

from sqlite3 import dbapi2 as sqlite


def getTableList(cx):
    cursor = cx.cursor()
    cursor.execute("select name from sqlite_master where type='table'")
    return [x[0] for x in cursor.fetchall()]


def getTableColumnList(cx, table):
    cursor = cx.cursor()
    cursor.execute("select * from %s" % table)
    return [x[0] for x in cursor.description]


def dumpTable(cx, dbFileName, table, fl):
    rx = re.compile("^insert into %s values" % table, re.IGNORECASE)

    columnList = getTableColumnList(cx, table)
    newText = "insert into %s(%s) values" % (table, ",".join(columnList))

    child = subprocess.Popen(["sqlite3", dbFileName], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    child.stdin.write(bytes(".mode insert %s\nselect * from %s;\n" % (table, table), 'utf-8'))
    child.stdin.close()

    for line in child.stdout.readlines():
        line = line.decode('utf-8')
        line = rx.sub(newText, line)
        fl.write(line)


def dumpDatabase(dbFileName, dumpFile):
    cx = sqlite.connect(os.path.abspath(dbFileName))
    for table in getTableList(cx):
        dumpTable(cx, dbFileName, table, dumpFile)


def main():
    dbFileName = sys.argv[1]
    dumpFileName = sys.argv[2]
    dumpFile = open(dumpFileName, "w", encoding='utf-8')
    dumpDatabase(dbFileName, dumpFile)


if __name__ == "__main__":
    main()
# vi: ts=4 sw=4 et
