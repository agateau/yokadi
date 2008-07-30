from db import *

from completers import *


class ProjectCmd(object):
    def do_p_rename(self, line):
        """Rename project.
        p_rename <old_name> <new_name>"""
        tokens = line.split(" ")
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
