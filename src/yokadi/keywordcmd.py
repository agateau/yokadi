# -*- coding: UTF-8 -*-
"""
Keyword related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
import tui

from db import Keyword
from yokadiexception import YokadiException, BadUsageException
from completers import KeywordCompleter
from sqlobject.dberrors import DuplicateEntryError
from sqlobject import LIKE

class KeywordCmd(object):
    def do_k_list(self, line):
        """List all keywords."""
        for keyword in Keyword.select():
            tasks = ", ".join(str(task.id) for task in keyword.tasks)
            print "%s (tasks: %s)" % (keyword.name, tasks)

    def do_k_add(self, line):
        """Add a keyword
        k_add @<keyword1> [@<keyword2>...]"""
        if not line:
            raise BadUsageException("You must provide at least one keyword name")
        for keyword in line.split():
            try:
                Keyword(name=keyword)
                print "Keyword %s has been created" % keyword
            except DuplicateEntryError:
                print "Keyword %s already exist" % keyword

    def do_k_remove(self, line):
        """Remove a keyword
        k_remove @<keyword>"""
        keyword = dbutils.getKeywordFromName(line)

        if keyword.tasks:
            print "The keyword %s is used by the following tasks: %s" % (keyword.name,
                                                                         ", ".join(str(task.id) for task in keyword.tasks))
            if tui.confirm("Do you really want to remove this keyword"):
                keyword.destroySelf()
                print "Keyword %s has been removed" % keyword.name

    complete_k_remove = KeywordCompleter(1)
