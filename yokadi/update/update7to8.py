# -*- coding: UTF-8 -*-
"""
Update from version 7 to version 8 of Yokadi DB
Drops the projectkeyword table, since we are removing this feature.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""


def dropProjectKeywordTable(cursor):
    cursor.execute('drop table project_keyword')


def update(cursor):
    dropProjectKeywordTable(cursor)


if __name__ == "__main__":
    import updateutils
    updateutils.main(update)
# vi: ts=4 sw=4 et
