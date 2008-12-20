# -*- coding: UTF-8 -*-
"""
Task related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""
import os

from db import Config, Keyword, Project, Task
from sqlobject import SQLObjectNotFound, LIKE, AND
import utils
import parseutils
import sys
import tui
from textrenderer import TextRenderer
from completers import ProjectCompleter, t_listCompleter, taskIdCompleter
from yokadiexception import YokadiException
from textlistrenderer import TextListRenderer
from xmllistrenderer import XmlListRenderer
from csvlistrenderer import CsvListRenderer
from htmllistrenderer import HtmlListRenderer
import colors as C
import dateutils

from datetime import datetime, date, timedelta

from yokadioptionparser import YokadiOptionParser

gRendererClassDict = dict(
    text=TextListRenderer,
    xml=XmlListRenderer,
    csv=CsvListRenderer,
    html=HtmlListRenderer)

class TaskCmd(object):
    __slots__ = ["renderer"]
    def __init__(self):
        self.renderer = TextRenderer()

    def do_t_add(self, line):
        """Add new task. Will prompt to create keywords if they do not exist.
        t_add <projectName> [-k <keyword1>] [-k <keyword2>] <Task description>"""
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

    complete_t_describe = taskIdCompleter

    def do_t_set_urgency(self, line):
        """Defines urgency of a task.
        t_set_urgency <id> <value>"""
        tokens = line.split(" ")
        if len(tokens)!=2:
            raise YokadiException("You must provide a taskId and an urgency value") 
        task = utils.getTaskFromId(tokens[0])
        try:
            # Do not use isdigit(), so that we can set negative urgency. This
            # make it possible to stick tasks to the bottom of the list.
            urgency = int(tokens[1])
        except ValueError:
            raise YokadiException("Task urgency must be a digit")
        task.urgency = urgency

    complete_t_set_urgency = taskIdCompleter

    def do_t_mark_started(self, line):
        """Mark task as started.
        t_mark_started <id>"""
        self._t_set_status(line, 'started')

    complete_t_mark_started = taskIdCompleter

    def do_t_mark_done(self, line):
        """Mark task as done.
        t_mark_done <id>"""
        self._t_set_status(line, 'done')

    complete_t_mark_done = taskIdCompleter

    def do_t_mark_new(self, line):
        """Mark task as new (not started).
        t_mark_new <id>"""
        self._t_set_status(line, 'new')

    complete_t_mark_new = taskIdCompleter

    def _t_set_status(self, line, status):
        task=utils.getTaskFromId(line)
        task.status = status
        if status == 'done':
            task.doneDate = datetime.now()
        else:
            task.doneDate = None
        print "Task '%s' marked as %s" % (task.title, status)

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

    complete_t_apply = taskIdCompleter

    def parser_t_remove(self):
        parser = YokadiOptionParser()
        parser.set_usage("t_remove [options] <id>")
        parser.set_description("Delete a task.")
        parser.add_option("-f", dest="force", default=False, action="store_true",
                          help="Skip confirmation prompt")
        return parser

    def do_t_remove(self, line):
        parser = self.parser_t_remove()
        options, args = parser.parse_args(line)
        task=utils.getTaskFromId(' '.join(args))
        if not options.force:
            if not tui.confirm("Remove task '%s'" % task.title):
                return
        projectId = task.project.id
        task.destroySelf()
        print "Task '%s' removed" % (task.title)

        # Delete project with no associated tasks
        if Task.select(Task.q.projectID == projectId).count() == 0:
            Project.delete(projectId)

    complete_t_remove = taskIdCompleter


    def parser_t_list(self):
        parser = YokadiOptionParser()
        parser.set_usage("t_list [options] <project_name>")
        parser.set_description(
            "List tasks filtered by project and/or keywords. "
            "'%' can be used as a wildcard in the project name: "
            "to list projects starting with 'foo', use 'foo%'.")

        parser.add_option("-a", "--all", dest="all",
                          default=False, action="store_true",
                          help="all tasks (done and to be done)")

        rangeList = ["today", "thisweek", "thismonth", "all"]
        parser.add_option("-d", "--done", dest="done",
                          help="only done tasks. <range> must be one of %s" % ", ".join(rangeList),
                          metavar="<range>")

        parser.add_option("-u", "--top-urgent", dest="topUrgent",
                          default=False, action="store_true",
                          help="top 5 urgent tasks of each project based on urgency")

        parser.add_option("-t", "--top-due", dest="topDue",
                          default=False, action="store_true",
                          help="top 5 urgent tasks of each project based on due date")

        parser.add_option("-k", "--keyword", dest="keyword",
                          action="append",
                          help="only list tasks matching <keyword>. If <value> is specified, <keyword> must have the same value",
                          metavar="<keyword>[=<value>]")

        formatList = ["auto"] + gRendererClassDict.keys()
        parser.add_option("--format", dest="format",
                          type="choice", default="auto", choices=formatList,
                          help="how should the task list be formated. <format> can be %s" % ", ".join(formatList),
                          metavar="<format>")
        parser.add_option("-o", "--output", dest="output",
                          help="Output task list to <file>",
                          metavar="<file>")
        return parser

    def do_t_list(self, line):
        doneRangeList= ["today", "thisweek", "thismonth"]

        def keywordDictIsSubsetOf(taskKeywordDict, wantedKeywordDict):
            # Returns true if taskKeywordDict is a subset of wantedKeywordDict
            # taskKeywordDict is considered a subset of wantedKeywordDict if:
            # 1. All wantedKeywordDict keys are in taskKeywordDict
            # 2. All wantedKeywordDict valued keywords have the same value
            #    in taskKeywordDict
            for wantedKeyword, wantedValue in wantedKeywordDict.items():
                if not wantedKeyword in taskKeywordDict:
                    return False
                if wantedValue and taskKeywordDict[wantedKeyword] != wantedValue:
                    return False
            return True

        def createFilterFromRange(_range):
            # Parse the _range string and return an SQLObject filter
            minDate = date.today()
            if _range == "today":
                pass
            elif _range == "thisweek":
                minDate -= timedelta(minDate.weekday())
            elif _range == "thismonth":
                minDate = minDate.replace(day = 1)
            else:
                raise YokadiException("Invalid range value '%s'" % _range)

            return Task.q.doneDate>=minDate

        def selectRendererClass():
            if options.format != "auto":
                return gRendererClassDict[options.format]

            defaultRendererClass = TextListRenderer
            if not options.output:
                return defaultRendererClass

            ext = os.path.splitext(options.output)[1]
            if not ext:
                return defaultRendererClass

            return gRendererClassDict.get(ext[1:], defaultRendererClass)

        #BUG: completion based on parameter position is broken when parameter is given
        parser = self.parser_t_list()
        options, args = parser.parse_args(line)
        if len(args) > 0:
            projectName = args[0]
        else:
            # Take all project if none provided
            projectName="%"
        projectList = Project.select(LIKE(Project.q.name, projectName))

        if projectList.count()==0:
            print C.RED + "Error: Found no project matching '%s'" % projectName + C.RESET
            return

        # Init keywordDict
        # Keyword object => None or value
        keywordDict = {}
        if options.keyword:
            for text in options.keyword:
                if "=" in text:
                    keyword, value = text.split("=", 1)
                    value = int(value)
                else:
                    keyword, value = text, None
                try:
                    Keyword.byName(keyword)
                    keywordDict[keyword] = value
                except SQLObjectNotFound:
                    print C.RED+"Warning: Keyword %s is unknown." % keyword+ C.RESET

        # Filtering and sorting according to parameters
        filters=[]
        order=-Task.q.urgency
        limit=None
        if options.done:
            filters.append(Task.q.status=='done')
            if options.done != "all":
                filters.append(createFilterFromRange(options.done))
        elif not options.all:
            filters.append(Task.q.status!='done')
        if options.topUrgent:
            order=-Task.q.urgency
            limit=5
        if options.topDue:
            filters.append(Task.q.dueDate!=None)
            order=Task.q.dueDate
            limit=5

        # Define output
        if options.output:
            out = open(options.output, "w")
        else:
            out = sys.stdout

        # Instantiate renderer
        rendererClass = selectRendererClass()
        renderer = rendererClass(out)

        # Fill the renderer
        hiddenProjectNames = []
        for project in projectList:
            if not project.active:
                hiddenProjectNames.append(project.name)
                continue
            taskList = Task.select(AND(Task.q.projectID == project.id, *filters),
                                   orderBy=order, limit=limit)

            if keywordDict:
                # FIXME: Optimize
                taskList = [x for x in taskList if keywordDictIsSubsetOf(x.getKeywordDict(), keywordDict)]
            else:
                taskList = list(taskList)

            if len(taskList) == 0:
                continue

            renderer.addTaskList(project, taskList)
        renderer.end()

        if len(hiddenProjectNames) > 0:
            print C.CYAN+"\nInfo"+C.RESET+": hidden projects: %s" % ", ".join(hiddenProjectNames)

    complete_t_list = t_listCompleter

    def do_t_reorder(self, line):
        """Reorder tasks of a project.
        It works by starting an editor with the task list: you can then change
        the order of the lines and save the list. The urgency field will be
        updated to match the order.
        t_reorder <project_name>"""
        if not line:
            line=Config.byName("DEFAULT_PROJECT").value
            print "Info: using default project (%s)" % line
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


    def parser_t_show(self):
        parser = YokadiOptionParser()
        parser.set_usage("t_show [options] <id>")
        parser.set_description("Display details of a task.")
        choices = ["all", "summary", "description"]
        parser.add_option("--output", dest="output", type="choice",
                          choices=choices,
                          default="all",
                          help="<output> can be one of %s. If not set, it defaults to all." % ", ".join(choices),
                          metavar="<output>")
        return parser

    def do_t_show(self, line):
        parser = self.parser_t_show()
        options, args = parser.parse_args(line)

        task=utils.getTaskFromId(' '.join(args))

        if options.output in ("all", "summary"):
            self.renderer.renderTaskSummary(task)

        if options.output in ("all", "description") and task.description:
            if options.output == "all":
                print
            print task.description

    complete_t_show = taskIdCompleter

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


    complete_t_edit = taskIdCompleter

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
        if len(line.split())<2:
            raise YokadiException("Give a task id and time, date or date & time")
        taskId, line=line.strip().split(" ", 1)
        task=utils.getTaskFromId(taskId)

        if line.lower()=="none":
            task.dueDate=None
        else:
            task.dueDate = dateutils.parseHumaneDateTime(line)

    complete_t_set_due = taskIdCompleter

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
