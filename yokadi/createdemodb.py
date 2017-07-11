#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Command line oriented, sqlite powered, todo list

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""
import os
import sys
from argparse import ArgumentParser

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.core import ydateutils

PROJECTS = ["birthday", "work", "home"]

KEYWORDS = ["phone", "grocery", "_note"]


def main():
    parser = ArgumentParser()
    parser.add_argument('db', metavar='<db>')
    args = parser.parse_args()

    dbname = args.db
    if os.path.exists(dbname):
        os.unlink(dbname)

    db.connectDatabase(dbname)
    db.setDefaultConfig()
    session = db.getSession()

    for name in PROJECTS:
        session.add(db.Project(name=name))

    for name in KEYWORDS:
        dbutils.getOrCreateKeyword(name, interactive=False)

    dbutils.addTask("birthday", "Buy food", {"grocery": None})
    dbutils.addTask("birthday", "Buy drinks", {"grocery": None})
    dbutils.addTask("birthday", "Invite Bob", {"phone": None})
    dbutils.addTask("birthday", "Invite Wendy", {"phone": None})
    dbutils.addTask("birthday", "Bake a yummy cake")
    dbutils.addTask("birthday", "Decorate living-room")

    task = dbutils.addTask("home", "Fix leak in the roof")
    task.dueDate = ydateutils.parseHumaneDateTime("-2d")

    dbutils.addTask("home", "Buy AAA batteries for kid toys", {"grocery": None})

    task = dbutils.addTask("home", "Bring the car to the garage")
    task.dueDate = ydateutils.parseHumaneDateTime("-1d")
    task.status = "done"

    task = dbutils.addTask("work", "Finish weekly report")
    task.dueDate = ydateutils.parseHumaneDateTime("+4d")
    task.description = """Include results from Acme department: http://acme.intranet/results.
    Don't forget to CC boss@acme.intranet.
    """

    session.commit()

    return 0


if __name__ == "__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
