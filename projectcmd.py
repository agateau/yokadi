# -*- coding: UTF-8 -*-
"""
Project related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

from db import Project
from completers import ProjectCompleter
from utils import YokadiException


class ProjectCmd(object):
    def do_p_rename(self, line):
        """Rename project.
        p_rename <old_name> <new_name>"""
        tokens = line.split(" ")
        if len(tokens)!=2:
            raise YokadiException("You must provide two arguments: old_name and new_name")
        oldName = tokens[0]
        newName = tokens[1]

        project = Project.selectBy(name=oldName)[0]
        project.name = newName
        print "Renamed project '%s' to '%s'" % (oldName, newName)
    complete_p_rename = ProjectCompleter(1)


    def do_p_list(self, line):
        """List all projects."""
        for project in Project.select():
            print project.name
# vi: ts=4 sw=4 et
