# -*- coding: UTF-8 -*-
"""
Update from version 1 to version 2 of Yokadi DB

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""


def createConfigTable(cursor):
    cursor.execute("""create table config (
        id integer not null,
        name varchar,
        value varchar,
        system boolean,
        "desc" varchar,
        primary key (id),
        unique (name),
        check (system in (0, 1))
);""")

    rows = [
        ("DB_VERSION", "2", True, "Database schema release number"),
        ("TEXT_WIDTH", "60", False, "Width of task display output with t_list command"),
        ("DEFAULT_PROJECT", "default", False, "Default project used when no project name given"),
        ("ALARM_DELAY_CMD", '''kdialog --sorry "task {TITLE} ({ID}) is due for {DATE}" --title "Yokadi Daemon"''',
         False, "Command executed by Yokadi Daemon when a tasks due date is reached soon (see ALARM_DELAY"),
        ("ALARM_DUE_CMD", '''kdialog --error "task {TITLE} ({ID}) should be done now" --title "Yokadi Daemon"''',
         False, "Command executed by Yokadi Daemon when a tasks due date is reached soon (see ALARM_DELAY")
    ]
    for name, value, system, desc in rows:
        system = 1 if system else 0
        cursor.execute("insert into config(name, value, system, \"desc\")\n"
                       "values (?, ?, ?, ?)", (name, value, system, desc))


def addProjectActiveColumn(cursor):
    cursor.execute("alter table project add column active boolean")
    cursor.execute("update project set active = 1")


def addTableDueDateColumn(cursor):
    cursor.execute("alter table task add column due_date datetime")


def update(cursor):
    createConfigTable(cursor)
    addProjectActiveColumn(cursor)
    addTableDueDateColumn(cursor)


if __name__ == "__main__":
    import updateutils
    updateutils.main(update)
# vi: ts=4 sw=4 et
