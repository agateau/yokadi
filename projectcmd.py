# -*- coding: UTF-8 -*-
"""
Project related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

from db import Project, Task
import utils
from completers import ProjectCompleter
from sqlobject import SQLObjectNotFound


class ProjectCmd(object):
    def do_p_rename(self, line):
        """Rename project.
        p_rename <old_name> <new_name>"""
        tokens = line.split(" ")
        if len(tokens)!=2:
            raise utils.YokadiException("You must provide two arguments: old_name and new_name")
        oldName = tokens[0]
        newName = tokens[1]

        project = utils.getProjectFromName(oldName, "old_name")
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
        utils.getProjectFromName(line).active=True
    complete_p_set_active = ProjectCompleter(1)

    def do_p_set_inactive(self, line):
        """Desactivate the given project"""
        utils.getProjectFromName(line).active=False
    complete_p_set_inactive = ProjectCompleter(1)

    def do_p_remove(self, line):
        """Remove a project and all its associated tasks
        p_remove <project_name>"""
        project = utils.getProjectFromName(line)
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
