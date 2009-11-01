# -*- coding: UTF-8 -*-
"""
Keyword related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
from db import Keyword
from yokadiexception import YokadiException
from completers import KeywordCompleter
from sqlobject.dberrors import DuplicateEntryError
from sqlobject import LIKE

class KeywordCmd(object):
    def do_k_list(self, line):
        """List all keywords."""
        for keyword in Keyword.select():
            tasks=", ".join(str(task.id) for task in keyword.tasks)
            print "%s (tasks: %s)" % (keyword.name, tasks)

    def do_k_add(self, line):
        """Add a keyword"""
        if not line:
            raise YokadiException("You should provide at least a keyword name")
        for keyword in line.split():
            try:
                Keyword(name=keyword)
                print "Keyword %s has been created" % keyword
            except DuplicateEntryError:
                print "Keyword %s already exist" % keyword

    def do_k_remove(self, line):
        """Remove a keyword"""
        keywords=Keyword.select(LIKE(Keyword.q.name, line))
        if keywords.count()==0:
            print "Sorry, no keyword name matching %s exists. Use k_list to see all defined keywords and k_add to create keywords" % line 
            return
        for keyword in keywords:
            if keyword.tasks:
                print "The keyword %s is used by the following tasks: %s" % (keyword.name,
                                                                             ", ".join(str(task.id) for task in keyword.tasks))
                answer=raw_input("Do you really want to remove this keyword ? (y/n)")
                if answer!="y":
                    print "Skipping deletion of keyword %s" % keyword.name
                    continue
            keyword.destroySelf()
            print "Keyword %s has been removed" % keyword.name

    complete_k_remove = KeywordCompleter(1)