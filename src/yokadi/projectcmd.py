# -*- coding: UTF-8 -*-
"""
Project related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
from sqlobject import SQLObjectNotFound
from sqlobject.dberrors import DuplicateEntryError

import tui
from completers import ProjectCompleter
from db import Project, Task
from yokadiexception import YokadiException
from yokadioptionparser import YokadiOptionParser
import parseutils
import dbutils


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
    def do_p_add(self, line):
        """Add new project. Will prompt to create keywords if they do not exist.
        p_add <projectName> [@<keyword1>] [@<keyword2>]"""
        if not line:
            print "Give at least a project name !"
            return
        projectName, garbage, keywordDict = parseutils.parseLine(line)
        if garbage:
            raise YokadiException("Cannot parse line, got garbage (%s)" % garbage)
        try:
            project = Project(name=projectName)
        except DuplicateEntryError:
            raise YokadiException("A project named %s already exists. Please find another name" % projectName)
        print "Added project '%s'" % projectName
        if not dbutils.createMissingKeywords(keywordDict.keys()):
            return None
        project.setKeywordDict(keywordDict)

    def do_p_edit(self, line):
        """Edit a project.
        p_edit <project name>"""
        project=dbutils.getOrCreateProject(line, createIfNeeded=False)

        if not project:
            raise YokadiException("Project does not exist.")

        # Create project line
        projectLine = parseutils.createLine(project.name, "", project.getKeywordDict())

        # Edit
        line = tui.editLine(projectLine)

        # Update project
        projectName, garbage, keywordDict = parseutils.parseLine(line)
        if garbage:
            raise YokadiException("Cannot parse line, got garbage (%s)" % garbage)
        if not dbutils.createMissingKeywords(keywordDict.keys()):
            return
        project.name = projectName
        project.setKeywordDict(keywordDict)

    complete_p_edit = ProjectCompleter(1)

    def do_p_list(self, line):
        """List all projects."""
        for project in Project.select():
            if project.active:
                active = ""
            else:
                active = "(inactive)"
            print "%s %s %s" % (project.name, project.getKeywordsAsString(), active)


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
