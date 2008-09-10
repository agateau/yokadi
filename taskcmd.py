# -*- coding: UTF-8 -*-
"""
Task related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""

from db import Keyword, Project, Task
from sqlobject import SQLObjectNotFound, LIKE, AND
import utils
import parseutils
import sys
import tui
from textrenderer import TextRenderer
from completers import ProjectCompleter, t_listCompleter
from utils import YokadiException, guessDateFormat, guessTimeFormat
import colors as C

from datetime import datetime, timedelta
from time import strptime

class TaskCmd(object):
    __slots__ = ["renderer"]
    def __init__(self):
        self.renderer = TextRenderer()

    def do_t_add(self, line):
        """Add new task. Will prompt to create keywords if they do not exist.
        t_add <projectName> [-p <keyword1>] [-p <keyword2>] <Task description>"""
        if not line:
            print "Give at least a task name !"
            return
        projectName, title, keywordDict = parseutils.parseTaskLine(line)
        if not title:
            raise YokadiException("You should give a task title")
        task = utils.addTask(projectName, title, keywordDict)
        if task:
            print "Added task '%s' (id=%d)" % (title, task.id)

    complete_t_add = ProjectCompleter(1)

    def do_t_describe(self, line):
        """Starts an editor to enter a longer description of a task.
        t_describe <id>"""
        task=utils.getTaskFromId(line)
        description = tui.editText(task.description)
        task.description = description

    def do_t_set_urgency(self, line):
        """Defines urgency of a task (0 -> 100).
        t_set_urgency <id> <value>"""
        tokens = line.split(" ")
        if len(tokens)!=2:
            raise YokadiException("You must provide a taskId and an urgency value") 
        task = utils.getTaskFromId(tokens[0])
        if tokens[1].isdigit():
            urgency = int(tokens[1])
            task.urgency = urgency
        else:
            raise YokadiException("Task urgency must be a digit")

    def do_t_mark_started(self, line):
        """Mark task as started.
        t_mark_started <id>"""
        task=utils.getTaskFromId(line)
        task.status = 'started'
        task.doneDate = None

    def do_t_mark_done(self, line):
        """Mark task as done.
        t_mark_done <id>"""
        task=utils.getTaskFromId(line)
        task.status = 'done'
        task.doneDate = datetime.now()

    def do_t_mark_new(self, line):
        """Mark task as new (not started).
        t_mark_new <id>"""
        task=utils.getTaskFromId(line)
        task.status = 'new'
        task.doneDate = None

    def do_t_apply(self, line):
        """Apply a command to several tasks.
        t_apply <id1>[,<id2>,[<id3>]...]] <command> <args>"""
        tokens = line.split(" ", 2)
        if len(tokens)<2:
            raise YokadiException("Give at least a task id and a command. See 'help t_apply'")
        idStringList = tokens[0]
        cmd = tokens[1]
        if len(tokens) == 3:
            args = tokens[2]
        else:
            args = ""
        ids = [int(x) for x in idStringList.split(",")]
        for id in ids:
            line = " ".join([cmd, str(id), args])
            self.onecmd(line.strip())

    def do_t_remove(self, line):
        """Delete a task.
        t_remove <id>"""
        task=utils.getTaskFromId(line)
        task.destroySelf()


    def do_t_list(self, line):
        """List tasks by project and/or keywords.
        t_list <project_name> [<keyword1> [<keyword2>]...]

        '%' can be used as a wildcard in the project name:
        - To list projects starting with "foo", use "foo%".
        - To list all projects, use "%".
        """
        tokens = line.strip().split(' ')
        projectName = tokens[0]
        if not projectName:
            # Take all project if none provided
            projectName="%"
        projectList = Project.select(LIKE(Project.q.name, projectName))

        if len(tokens) > 1:
            keywordSet = set()
            for k in tokens[1:]:
                try:
                    keywordSet.add(Keyword.byName(k))
                except SQLObjectNotFound:
                    print C.RED+"Warning: Keyword %s is unknown." % k + C.RESET

        else:
            keywordSet = None

        for project in projectList:
            if not project.active:
                print C.CYAN+"\nInfo"+C.RESET+": project %s is hidden because it is inactive. Use p_set_active to activate it\n" % project.name
                continue
            taskList = Task.select(AND(Task.q.projectID == project.id,
                                       Task.q.status    != 'done'),
                                   orderBy=-Task.q.urgency)

            if keywordSet:
                # FIXME: Optimize
                taskList = [x for x in taskList if keywordSet.issubset(set(x.keywords))]
            else:
                taskList = list(taskList)

            if len(taskList) == 0:
                continue

            self.renderer.renderTaskListHeader(project.name)
            for task in taskList:
                self.renderer.renderTaskListRow(task)

    complete_t_list = t_listCompleter

    def do_t_reorder(self, line):
        """Reorder tasks of a project.
        It works by starting an editor with the task list: you can then change
        the order of the lines and save the list. The urgency field will be
        updated to match the order.
        t_reorder <project_name>"""
        if not line:
            print "Info: using default project"
            line="default"
        project = Project.byName(line)
        taskList = Task.select(AND(Task.q.projectID == project.id,
                                   Task.q.status    != 'done'),
                               orderBy=-Task.q.urgency)
        lines = [ "%d,%s" % (x.id, x.title) for x in taskList]
        text = tui.editText("\n".join(lines))

        ids = []
        for line in text.split("\n"):
            line = line.strip()
            if not "," in line:
                continue
            id = int(line.split(",")[0])
            ids.append(id)

        ids.reverse()
        for urgency, id in enumerate(ids):
            task = Task.get(id)
            task.urgency = urgency

    complete_t_reorder = ProjectCompleter(1)


    def do_t_show(self, line):
        """Display details of a task.
        t_show <id>"""
        task=utils.getTaskFromId(line)
        self.renderer.renderTaskDetails(task)


    def do_t_edit(self, line):
        """Edit a task.
        t_edit <id>"""
        task=utils.getTaskFromId(line)

        # Create task line
        taskLine = parseutils.createTaskLine(task.project.name, task.title, task.getKeywordDict())

        # Edit
        line = tui.editLine(taskLine)

        # Update task
        projectName, title, keywordDict = parseutils.parseTaskLine(line)
        if not utils.createMissingKeywords(keywordDict.keys()):
            return
        task.project = utils.getOrCreateProject(projectName)
        task.title = title
        task.setKeywordDict(keywordDict)


    def do_t_set_project(self, line):
        """Set task's project.
        t_set_project <id> <project>"""
        tokens = line.split(" ")
        if len(tokens)!=2:
            raise YokadiException("You should give two arguments: <task id> <project>")
        task=utils.getTaskFromId(tokens[0])
        projectName = tokens[1]

        task.project = utils.getOrCreateProject(projectName)
        if task.project:
            print "Moved task '%s' to project '%s'" % (task.title, projectName)
    complete_t_set_project = ProjectCompleter(2)

    def do_t_set_due(self, line):
        """Set task's due date
        t_set_due_date <id> <date>"""
        # Date & Time format
        fDate=None
        fTime=None
        if len(line.split())<2:
            raise YokadiException("Give a task id and time, date or date & time")
        taskId, line=line.strip().split(" ", 1)
        task=utils.getTaskFromId(taskId)

        if line.lower()=="none":
            task.dueDate=None
            return

        #TODO: make all the date stuff in a separate function to be reusable easily (set_creation_date ?)
        today=datetime.today().replace(microsecond=0)

        # Initialise dueDate to now (may be now + fixe delta ?)
        dueDate=today # Safe because datetime objects are immutables

        if line.startswith("+"):
            #Delta/relative date and/or time
            line=line.upper().strip("+")
            try:
                if   line.endswith("W"):
                    dueDate=today+timedelta(days=float(line[0:-1])*7)
                elif line.endswith("D"):
                    dueDate=today+timedelta(days=float(line[0:-1]))
                elif line.endswith("H"):
                    dueDate=today+timedelta(hours=float(line[0:-1]))
                elif line.endswith("M"):
                    dueDate=today+timedelta(minutes=float(line[0:-1]))
                else:
                    raise YokadiException("Unable to understand time shift. See help t_set_due")
            except ValueError:
                raise YokadiException("Timeshift must be a float or an integer")
        else:
            #Absolute date and/or time
            if " " in line:
                # We assume user give date & time
                tDate, tTime=line.split()
                fDate=guessDateFormat(tDate)
                fTime=guessTimeFormat(tTime)
                try:
                    dueDate=datetime(*strptime(line, "%s %s" % (fDate, fTime))[0:5])
                except Exception, e:
                    raise YokadiException("Unable to understand date & time format:\t%s" % e)
            else:
                if ":" in line:
                    fTime=guessTimeFormat(line)
                    tTime=datetime(*strptime(line, fTime)[0:5]).time()
                    dueDate=datetime.combine(today, tTime)
                else:
                    fDate=guessDateFormat(line)
                    dueDate=datetime(*strptime(line, fDate)[0:5])
            if fDate:
                # Set year and/or month to current date if not given
                if not "%Y" in fDate:
                    dueDate=dueDate.replace(year=today.year)
                if not "%M" in fDate:
                    dueDate=dueDate.replace(month=today.month)
        # Set the due date
        task.dueDate=dueDate

    def do_t_export(self, line):
        """Export all tasks of all projects in various format
            t_export csv mytasks.csv
            t_export html mytasks.html
            t_export xml mystasks.xml
        If filename is ommited, tasks are printed on screen"""
        line=line.split()
        if   len(line)<1:
            raise YokadiException("You should at least specify the format (csv, html or xml)")
        elif len(line)==1:
            filePath=None
        else:
            filePath=line[1]
        format=line[0].lower()
        utils.exportTasks(format, filePath)

# vi: ts=4 sw=4 et
