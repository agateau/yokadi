# -*- coding: UTF-8 -*-
"""
Project related commands.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from yokadi.ycli import tui
from yokadi.ycli.completers import ProjectCompleter
from yokadi.ycli import parseutils
from yokadi.core import db
from yokadi.core.db import Project, Task
from yokadi.core.yokadiexception import YokadiException, BadUsageException
from yokadi.core.yokadioptionparser import YokadiOptionParser
from yokadi.core import dbutils


def getProjectFromName(name, parameterName="project_name"):
    """
    Helper function which returns a project given its name, or raise a
    YokadiException if it does not exist.
    """
    name = name.strip()
    if len(name) == 0:
        raise BadUsageException("Missing <%s> parameter" % parameterName)

    try:
        session = db.getSession()
        return session.query(Project).filter_by(name=name).one()
    except NoResultFound:
        raise YokadiException("Project '%s' not found. Use p_list to see all projects." % name)


class ProjectCmd(object):
    def do_p_add(self, line):
        """Add new project.
        p_add <projectName>"""
        if not line:
            print("Missing project name.")
            return
        projectName = parseutils.parseProjectName(line)
        session = db.getSession()
        try:
            project = Project(name=projectName)
            session.add(project)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise YokadiException("A project named %s already exists. Please find another name" % projectName)
        print("Added project '%s'" % projectName)

    def do_p_edit(self, line):
        """Edit a project.
        p_edit <project name>"""
        session = db.getSession()
        project = dbutils.getOrCreateProject(line, createIfNeeded=False)

        if not project:
            raise YokadiException("Project does not exist.")

        # Edit
        line = tui.editLine(project.name)

        # Update project
        projectName = parseutils.parseProjectName(line)
        try:
            project.name = projectName
            session.commit()
        except IntegrityError:
            session.rollback()
            raise YokadiException("A project named %s already exists. Please find another name" % projectName)

    complete_p_edit = ProjectCompleter(1)

    def do_p_list(self, line):
        """List all projects."""
        session = db.getSession()
        for project in session.query(Project).all():
            if project.active:
                active = ""
            else:
                active = "(inactive)"
            print("%s %s %s" % (project.name.ljust(20), str(session.query(Task).filter_by(project=project).count()).rjust(4), active))

    def do_p_set_active(self, line):
        """Activate the given project"""
        session = db.getSession()
        project = getProjectFromName(line)
        project.active = True
        session.merge(project)
        session.commit()
    complete_p_set_active = ProjectCompleter(1)

    def do_p_set_inactive(self, line):
        """Desactivate the given project"""
        session = db.getSession()
        project = getProjectFromName(line)
        project.active = False
        session.merge(project)
        session.commit()
    complete_p_set_inactive = ProjectCompleter(1)

    def parser_p_remove(self):
        parser = YokadiOptionParser()
        parser.usage = "p_remove [options] <project_name>"
        parser.description = "Remove a project and all its associated tasks."
        parser.add_argument("-f", dest="force", default=False, action="store_true",
                          help="Skip confirmation prompt")
        parser.add_argument("project")
        return parser

    def do_p_remove(self, line):
        session = db.getSession()
        parser = self.parser_p_remove()
        args = parser.parse_args(line)
        project = getProjectFromName(args.project)
        nbTasks = len(project.tasks)
        if not args.force:
            if not tui.confirm("Remove project '%s' and its %d tasks" % (project.name, nbTasks)):
                return
        session.delete(project)
        session.commit()
        print("Project removed")
    complete_p_remove = ProjectCompleter(1)

# vi: ts=4 sw=4 et
