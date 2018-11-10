# -*- coding: UTF-8 -*-
"""
Update from version 4 to version 5 of Yokadi DB

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or newer
"""


def updateBugsKeywordsNames(cursor):
    for keyword in ("bug", "severity", "likelihood"):
        cursor.execute("update keyword set name='_%s' where name='%s'" % (keyword, keyword))


def removeTextWidthParam(cursor):
    cursor.execute("delete from config where name='TEXT_WIDTH'")


def update(cursor):
    updateBugsKeywordsNames(cursor)
    removeTextWidthParam(cursor)


if __name__ == "__main__":
    import updateutils
    updateutils.main(update)
# vi: ts=4 sw=4 et
