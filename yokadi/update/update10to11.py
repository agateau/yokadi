"""
Update from version 10 to version 11 of Yokadi DB

- Make the tuple (task_id, keyword_id) unique in TaskKeyword

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""
from collections import defaultdict

from yokadi.update import updateutils


def removeTaskKeywordDuplicates(cursor):
    sql = "select id, task_id, keyword_id from task_keyword"

    # Create a dict of (task_id, keyword_id) => [id...]
    dct = defaultdict(list)
    for row in cursor.execute(sql).fetchall():
        tk_id, task_id, keyword_id = row
        dct[(task_id, keyword_id)].append(tk_id)

    # Delete all extra ids
    for (task_id, keyword_id), tk_ids in dct.items():
        for tk_id in tk_ids[1:]:
            cursor.execute("delete from task_keyword where id = ?", (tk_id,))


def update(cursor):
    removeTaskKeywordDuplicates(cursor)


if __name__ == "__main__":
    updateutils.main(update)
# vi: ts=4 sw=4 et
