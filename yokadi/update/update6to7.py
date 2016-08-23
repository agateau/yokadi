# -*- coding: UTF-8 -*-
"""
Update from version 6 to version 7 of Yokadi DB
This one is empty, database schema don't change
but we want to prevent use of SQLObject against a database created with SQLAlchemy
because SQLObject cannot read timestamps written by SQLAlchemy

@author: Benjamin Port <contact@benjaminport.fr>
@license: GPL v3 or newer
"""


def update(dbpath):
    pass


if __name__ == "__main__":
    pass
# vi: ts=4 sw=4 et
