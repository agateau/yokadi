#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Generates a data-only sqlite dump, with insert statements including column
names.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""

import os
import re
import sqlite3
import subprocess
import sys


def getTableList(cx):
    cursor = cx.cursor()
    cursor.execute("select name from sqlite_master where type='table' and name!='sqlite_sequence'")
    return [x[0] for x in cursor.fetchall()]


def getTableColumnList(cx, table):
    cursor = cx.cursor()
    cursor.execute("select * from %s" % table)
    return [x[0] for x in cursor.description]


def dumpTable(cx, dbFileName, table, fl):
    # Prepare a regeex to insert column names in the `insert` statement. This
    # ensures values are correctly inserted even if the columns are not in the
    # same order in the dumped and the restored table.
    rx = re.compile("^insert into %s values" % table, re.IGNORECASE)
    columnList = getTableColumnList(cx, table)
    newText = "insert into %s(%s) values" % (table, ",".join(columnList))

    # Tell sqlite3 to print `insert` statements for the table
    child = subprocess.Popen(["sqlite3", dbFileName], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    child.stdin.write(bytes(".mode insert %s\nselect * from %s;\n" % (table, table), 'utf-8'))
    child.stdin.close()

    for line in child.stdout.readlines():
        line = line.decode('utf-8')
        line = rx.sub(newText, line)
        fl.write(line)


def dumpDatabase(dbFileName, dumpFile):
    cx = sqlite3.connect(os.path.abspath(dbFileName))
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
