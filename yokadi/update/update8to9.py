# -*- coding: UTF-8 -*-
"""
Update from version 8 to version 9 of Yokadi DB

- Delete invalid TaskKeyword rows
- Move aliases to an Alias table
- Add an uuid column to Task and Project tables

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""
from uuid import uuid1


def deleteInvalidTaskKeywordRows(cursor):
    cursor.execute('delete from task_keyword where task_id is null or keyword_id is null')


def addAliasTable(cursor):
    cursor.execute("""create table alias (
        uuid varchar not null primary key,
        name varchar not null,
        command varchar not null,
        unique(name)
    )""")


def migrateAliases(cursor):
    row = cursor.execute("select value from config where name = 'ALIASES'").fetchone()
    if not row:
        return

    aliasesString = row[0]
    try:
        aliases = eval(aliasesString)
    except Exception:
        # Failed to parse aliases
        print("Failed to parse v9 aliases: {}".format(aliasesString))
        return
    for name, command in aliases.items():
        uuid = str(uuid1())
        cursor.execute("insert into alias(uuid, name, command) values(?, ?, ?)", (uuid, name, command))

    cursor.execute("delete from config where name = 'ALIASES'")


def addUuidColumn(cursor, tableName):
    cursor.execute("alter table {} add column uuid varchar".format(tableName))
    for row in cursor.execute("select id from {}".format(tableName)).fetchall():
        id = row[0]
        uuid = str(uuid1())
        cursor.execute("update {} set uuid = ? where id = ?".format(tableName), (uuid, id))


def update(cursor):
    deleteInvalidTaskKeywordRows(cursor)
    addAliasTable(cursor)
    migrateAliases(cursor)
    addUuidColumn(cursor, "project")
    addUuidColumn(cursor, "task")


if __name__ == "__main__":
    import updateutils
    updateutils.main(update)
# vi: ts=4 sw=4 et
