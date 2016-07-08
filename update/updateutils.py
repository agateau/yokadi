"""
Utilities to handle database schema updates

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""
import os
import re
import sqlite3
import subprocess
import sys


def getTableList(cursor):
    cursor.execute("select name from sqlite_master where type='table' and name!='sqlite_sequence'")
    return [x[0] for x in cursor.fetchall()]


def getTableColumnList(cursor, table):
    cursor.execute("select * from %s" % table)
    return [x[0] for x in cursor.description]


def dumpTable(cursor, dbFileName, table, fl):
    # Prepare a regeex to insert column names in the `insert` statement. This
    # ensures values are correctly inserted even if the columns are not in the
    # same order in the dumped and the restored table.
    rx = re.compile("^insert into %s values" % table, re.IGNORECASE)
    columnList = getTableColumnList(cursor, table)
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
    conn = sqlite3.connect(os.path.abspath(dbFileName))
    cursor = conn.cursor()
    for table in getTableList(cursor):
        dumpTable(cursor, dbFileName, table, dumpFile)


def main(function):
    """
    Runs an update function on a database. Useful as a test main
    """
    dbpath = sys.argv[1]
    with sqlite3.connect(dbpath) as conn:
        function(conn.cursor())
