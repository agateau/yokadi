"""
Utilities to handle database schema updates

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""
import sqlite3
import sys


class UpdateError(Exception):
    pass


class UpdateCanceledError(UpdateError):
    def __init__(self):
        super(UpdateError, self).__init__("Canceled")


def getTableList(cursor):
    cursor.execute("select name from sqlite_master where type='table' and name!='sqlite_sequence'")
    return [x[0] for x in cursor.fetchall()]


def getTableColumnList(cursor, table):
    cursor.execute("select * from %s" % table)
    return [x[0] for x in cursor.description]


def deleteTableColumns(cursor, table, columnsToDelete):
    columnList = getTableColumnList(cursor, table)
    for column in columnsToDelete:
        columnList.remove(column)
    columns = ",".join(columnList)
    sqlCommands = (
        "create temporary table {table}_backup({columns})",
        "insert into {table}_backup select {columns} from {table}",
        "drop table {table}",
        "create table {table}({columns})",
        "insert into {table} select {columns} from {table}_backup",
        "drop table {table}_backup",
    )
    for sql in sqlCommands:
        cursor.execute(sql.format(table=table, columns=columns))


def main(function):
    """
    Runs an update function on a database. Useful as a test main
    """
    dbpath = sys.argv[1]
    with sqlite3.connect(dbpath) as conn:
        function(conn.cursor())
