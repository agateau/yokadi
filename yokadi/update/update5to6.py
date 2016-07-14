# -*- coding: UTF-8 -*-
"""
Update from version 5 to version 6 of Yokadi DB

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or newer
"""
from sqlite3 import OperationalError


def createTaskLockTable(cursor):
    cursor.execute("""
create table task_lock (
    id integer not null,
    task_id integer,
    pid integer,
    update_date datetime,
    primary key (id),
    unique (task_id),
    foreign key(task_id) references task (id)
)
""")


def removeTaskTitleUniqConstraint(cursor):
    try:
        cursor.execute("drop index task_uniqTaskTitlePerProject")
    except OperationalError as exc:
        if str(exc) == "no such index: task_uniqTaskTitlePerProject":
            pass


def update(cursor):
    removeTaskTitleUniqConstraint(cursor)
    createTaskLockTable(cursor)


if __name__ == "__main__":
    import updateutils
    updateutils.main(update)
# vi: ts=4 sw=4 et
