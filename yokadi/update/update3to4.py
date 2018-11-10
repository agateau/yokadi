# -*- coding: UTF-8 -*-
"""
Update from version 3 to version 4 of Yokadi DB

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or newer
"""


def createRecurrenceTable(cursor):
    cursor.execute("""
create table recurrence (
    id integer not null,
    rule varchar,
    primary key (id)
)
""")


def addTaskRecurrenceIdColumn(cursor):
    cursor.execute("alter table task add column recurrence_id integer references recurrence(id)")


def removeDefaultProject(cursor):
    cursor.execute("delete from config where name='DEFAULT_PROJECT'")


def update(cursor):
    createRecurrenceTable(cursor)
    addTaskRecurrenceIdColumn(cursor)
    removeDefaultProject(cursor)


if __name__ == "__main__":
    import updateutils
    updateutils.main(update)
# vi: ts=4 sw=4 et
