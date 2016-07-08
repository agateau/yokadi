# -*- coding: UTF-8 -*-
"""
Update from version 9 to version 10 of Yokadi DB

- Remove Task.recurrence_id column
- Add Task.recurrence column
- Import recurrence from the Recurrence table
- Remove Recurrence table

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""
import json
import pickle


def tuplify(value):
    if value is None:
        return ()
    if isinstance(value, int):
        return (value,)
    else:
        return tuple(value)


def createByweekdayValue(rule):
    if rule._bynweekday:
        # Special case: recurrence every 1st, 2nd, 3rd, 4th or last $weekday of month
        weekday, pos = rule._bynweekday[0]
        return dict(weekday=weekday, pos=pos)

    return tuplify(rule._byweekday)


def createDictFromRule(pickledRule):
    rule = pickle.loads(pickledRule)
    dct = {}
    dct["freq"] = rule._freq
    dct["bymonth"] = tuplify(rule._bymonth)
    dct["bymonthday"] = tuplify(rule._bymonthday)
    dct["byweekday"] = createByweekdayValue(rule)
    dct["byhour"] = tuplify(rule._byhour)
    dct["byminute"] = tuplify(rule._byminute)
    return dct


def addRecurrenceColumn(cursor):
    cursor.execute("alter table task add column recurrence")
    sql = "select t.id, r.rule from task t left join recurrence r on t.recurrence_id = r.id"
    for row in cursor.execute(sql).fetchall():
        id, pickledRule = row
        if pickledRule:
            try:
                dct = createDictFromRule(bytes(pickledRule, "utf-8"))
            except Exception as exc:
                print("Failed to import recurrence for task {}: {}".format(id, exc))
                dct = {}
        else:
            dct = {}
        ruleStr = json.dumps(dct)

        cursor.execute("update task set recurrence = ? where id = ?", (ruleStr, id))


def deleteRecurrenceTable(cursor):
    cursor.execute("drop table recurrence")


def deleteTableColumn(cursor, table, columnsToKeep):
    columns = ",".join(columnsToKeep)
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


def update(cursor):
    taskColumnList = (
        "id", "uuid", "title", "creation_date", "due_date", "done_date",
        "description", "urgency", "status", "recurrence", "project_id",
    )
    addRecurrenceColumn(cursor)
    deleteRecurrenceTable(cursor)
    deleteTableColumn(cursor, "task", taskColumnList)


if __name__ == "__main__":
    import updateutils
    updateutils.main(update)
# vi: ts=4 sw=4 et
