# -*- coding: UTF-8 -*-
"""
Project related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
from sqlobject import SQLObjectNotFound

import tui
from completers import ProjectCompleter
from db import Project, Task
from yokadiexception import YokadiException
from yokadioptionparser import YokadiOptionParser


def getProjectFromName(name, parameterName="project_name"):
    """
    Helper function which returns a project given its name, or raise a
    YokadiException if it does not exist.
    """
    name = name.strip()
    if len(name) == 0:
        raise YokadiException("Missing <%s> parameter" % parameterName)

    try:
        return Project.byName(name)
    except SQLObjectNotFound:
        raise YokadiException("Project '%s' not found. Use p_list to see all projects." % name)


class ProjectCmd(object):
    def do_p_rename(self, line):
        """Rename project.
        p_rename <old_name> <new_name>"""
        tokens = line.split(" ")
        if len(tokens)!=2:
            raise YokadiException("You must provide two arguments: old_name and new_name")
        oldName = tokens[0]
        newName = tokens[1]

        project = getProjectFromName(oldName, "old_name")
        project.name = newName
        print "Renamed project '%s' to '%s'" % (oldName, newName)
    complete_p_rename = ProjectCompleter(1)


    def do_p_list(self, line):
        """List all projects."""
        for project in Project.select():
            if project.active:
                print project.name
            else:
                print "%s (inactive)" % project.name

    def do_p_set_active(self, line):
        """Activate the given project"""
        getProjectFromName(line).active=True
    complete_p_set_active = ProjectCompleter(1)

    def do_p_set_inactive(self, line):
        """Desactivate the given project"""
        getProjectFromName(line).active=False
    complete_p_set_inactive = ProjectCompleter(1)

    def parser_p_remove(self):
        parser = YokadiOptionParser()
        parser.set_usage("p_remove [options] <project_name>")
        parser.set_description("Remove a project and all its associated tasks.")
        parser.add_option("-f", dest="force", default=False, action="store_true",
                          help="Skip confirmation prompt")
        return parser

    def do_p_remove(self, line):
        parser = self.parser_p_remove()
        options, args = parser.parse_args(line)
        project = getProjectFromName(' '.join(args))
        if not options.force:
            if not tui.confirm("Remove project '%s' and all its tasks" % project.name):
                return
        taskList = Task.select(Task.q.projectID == project.id)
        taskList = list(taskList)
        print "Removing project tasks:"
        for task in taskList:
            task.delete(task.id)
            print "- task %(id)-3s: %(title)-30s" % dict(id=str(task.id), title=str(task.title))
        project.delete(project.id)
        print "Project removed"
    complete_p_remove = ProjectCompleter(1)
# vi: ts=4 sw=4 et