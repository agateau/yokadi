# -*- coding: UTF-8 -*-
"""
Task related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""
from cmd import Cmd
from datetime import datetime

from db import *
import utils
import parseutils
import tui
from textrenderer import TextRenderer
from completers import *
from utils import YokadiException

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
        task = utils.addTask(projectName, title, keywordDict)
        if task:
            print "Added task '%s' (id=%d)" % (title, task.id)

    complete_t_add = ProjectCompleter(1)

    def do_t_describe(self, line):
        """Starts an editor to enter a longer description of a task.
        t_describe <id>"""
        taskId=self.providesTaskId(line, existingTask=True)
        task = Task.get(taskId)
        ok, description = tui.editText(task.description)
        if ok:
            task.description = description
        else:
            print "Starting editor failed"

    def do_t_set_urgency(self, line):
        """Defines urgency of a task (0 -> 100).
        t_set_urgency <id> <value>"""
        tokens = line.split(" ")
        taskId = int(tokens[0])
        urgency = int(tokens[1])
        task = Task.get(taskId)
        task.urgency = urgency

    def do_t_mark_started(self, line):
        """Mark task as started.
        t_mark_started <id>"""
        taskId=self.providesTaskId(line, existingTask=True)
        task = Task.get(taskId)
        task.status = 'started'
        task.doneDate = None

    def do_t_mark_done(self, line):
        """Mark task as done.
        t_mark_done <id>"""
        taskId=self.providesTaskId(line, existingTask=True)
        task = Task.get(taskId)
        task.status = 'done'
        task.doneDate = datetime.now()

    def do_t_mark_new(self, line):
        """Mark task as new (not started).
        t_mark_new <id>"""
        taskId=self.providesTaskId(line, existingTask=True)
        task = Task.get(taskId)
        task.status = 'new'
        task.doneDate = None

    def do_t_apply(self, line):
        """Apply a command to several tasks.
        t_apply <id1>[,<id2>,[<id3>]...]] <command> <args>"""
        tokens = line.split(" ", 2)
        if len(tokens)<2:
            raise YokadiException("Give at least a task id and a command. See 'help t_apply'")
            return
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
        taskId=self.providesTaskId(line, existingTask=True)
        Task.delete(taskId)
        

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
            keywordSet = set([Keyword.byName(x) for x in tokens[1:]])
        else:
            keywordSet = None

        for project in projectList:
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

    complete_t_list = ProjectCompleter(1)

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
        ok, text = tui.editText("\n".join(lines))
        if not ok:
            return

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
        taskId=self.providesTaskId(line, existingTask=True)
        task = Task.get(taskId)
        self.renderer.renderTaskDetails(task)


    def do_t_edit(self, line):
        """Edit a task.
        t_edit <id>"""
        taskId=self.providesTaskId(line, existingTask=True)
        task = Task.get(taskId)

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
        taskId = int(tokens[0])
        projectName = tokens[1]

        task = Task.get(taskId)
        task.project = utils.getOrCreateProject(projectName)
        if task.project:
            print "Moved task '%s' to project '%s'" % (task.title, projectName)
    complete_t_set_project = ProjectCompleter(2)

    def providesTaskId(self, line, existingTask=True):
        if not line:
            raise YokadiException("Provide a task id")
        taskId = int(line)
        if existingTask:
            try:
                task = Task.get(taskId)
            except SQLObjectNotFound:
                raise YokadiException("Task %s does not exist. Use t_list to see all tasks" % taskId)
        return taskId
# vi: ts=4 sw=4 et
