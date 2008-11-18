# -*- coding: UTF-8 -*-
"""
Project related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

from db import Project, Task
from completers import ProjectCompleter
from utils import YokadiException
from sqlobject import SQLObjectNotFound


def projectByName(name, parameterName="project_name"):
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

        project = projectByName(oldName, "old_name")
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
        projectByName(line).active=True
    complete_p_set_active = ProjectCompleter(1)

    def do_p_set_inactive(self, line):
        """Desactivate the given project"""
        projectByName(line).active=False
    complete_p_set_inactive = ProjectCompleter(1)

    def do_p_remove(self, line):
        """Remove a project and all its associated tasks
        p_remove <project_name>"""
        project = projectByName(line)
        taskList = Task.select(Task.q.projectID == project.id)
        taskList = list(taskList)
        print "Deleting project tasks:"
        for task in taskList:
            task.delete(task.id)
            print "- task %(id)-3s: %(title)-30s" % dict(id=str(task.id), title=str(task.title))
        project.delete(project.id)
        print "Project deleted"
    complete_p_remove = ProjectCompleter(1)
# vi: ts=4 sw=4 et
