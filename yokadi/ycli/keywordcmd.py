# -*- coding: UTF-8 -*-
"""
Keyword related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
from sqlalchemy.exc import IntegrityError

from yokadi.core import dbutils
from yokadi.ycli import tui

from yokadi.core import db
from yokadi.core.db import Keyword
from yokadi.core.yokadiexception import BadUsageException
from yokadi.ycli.completers import KeywordCompleter


class KeywordCmd(object):
    def do_k_list(self, line):
        """List all keywords."""
        for keyword in db.getSession().query(Keyword).all():
            tasks = ", ".join(str(task.id) for task in keyword.tasks)
            print("%s (tasks: %s)" % (keyword.name, tasks))

    def do_k_add(self, line):
        """Add a keyword
        k_add @<keyword1> [@<keyword2>...]"""
        session = db.getSession()
        if not line:
            raise BadUsageException("You must provide at least one keyword name")
        for keyword in line.split():
            try:
                session.add(Keyword(name=keyword))
                session.commit()
                print("Keyword %s has been created" % keyword)
            except IntegrityError:
                session.rollback()
                print("Keyword %s already exist" % keyword)

    def do_k_remove(self, line):
        """Remove a keyword
        k_remove @<keyword>"""
        session = db.getSession()
        keyword = dbutils.getKeywordFromName(line)

        if keyword.tasks:
            print("The keyword %s is used by the following tasks: %s" % (keyword.name,
                                                                         ", ".join(str(task.id) for task in keyword.tasks)))
            if tui.confirm("Do you really want to remove this keyword"):
                session.delete(keyword)
                session.commit()
                print("Keyword %s has been removed" % keyword.name)

    complete_k_remove = KeywordCompleter(1)

    def do_k_edit(self, line):
        """Edit a keyword
        k_edit @<keyword>"""
        session = db.getSession()
        keyword = dbutils.getKeywordFromName(line)
        oldName = keyword.name
        newName = tui.editLine(oldName)
        if newName == "":
            print("Cancelled")
            return

        lst = session.query(Keyword).filter_by(name=newName).all()
        if len(lst) == 0:
            # Simple case: newName does not exist, just rename the existing keyword
            keyword.name = newName
            session.merge(keyword)
            session.commit()
            print("Keyword %s has been renamed to %s" % (oldName, newName))
            return

        # We already have a keyword with this name, we need to merge
        print("Keyword %s already exists" % newName)
        if not tui.confirm("Do you want to merge %s and %s" % (oldName, newName)):
            return

        # Check we can merge
        conflictingTasks = []
        for task in keyword.tasks:
            kwDict = task.getKeywordDict()
            if oldName in kwDict and newName in kwDict and kwDict[oldName] != kwDict[newName]:
                conflictingTasks.append(task)

        if len(conflictingTasks) > 0:
            # We cannot merge
            tui.error("Cannot merge keywords %s and %s because they are both used with different values in these tasks:" % (oldName, newName))
            for task in conflictingTasks:
                print("- %d, %s" % (task.id, task.title))
            print("Edit these tasks and try again")
            return

        # Merge
        for task in keyword.tasks:
            kwDict = task.getKeywordDict()
            if not newName in kwDict:
                kwDict[newName] = kwDict[oldName]
            del kwDict[oldName]
            task.setKeywordDict(kwDict)
        session.delete(keyword)
        session.commit()
        print("Keyword %s has been merged with %s" % (oldName, newName))

    complete_k_edit = KeywordCompleter(1)
