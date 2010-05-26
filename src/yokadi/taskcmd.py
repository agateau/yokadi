# -*- coding: UTF-8 -*-
"""
Task related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import os
import readline
from datetime import datetime, timedelta
from dateutil import rrule
from sqlobject import LIKE, AND, OR, NOT
from sqlobject.sqlbuilder import LEFTJOINOn

from db import Config, Keyword, Project, Task, \
               TaskKeyword, Recurrence
import bugutils
import dbutils
import ydateutils
import parseutils
import tui
from completers import ProjectCompleter, projectAndKeywordCompleter, \
                       taskIdCompleter, recurrenceCompleter, dueDateCompleter
from yokadiexception import YokadiException, BadUsageException
from textlistrenderer import TextListRenderer
from xmllistrenderer import XmlListRenderer
from csvlistrenderer import CsvListRenderer
from htmllistrenderer import HtmlListRenderer
from plainlistrenderer import PlainListRenderer
from yokadioptionparser import YokadiOptionParser

gRendererClassDict = dict(
    text=TextListRenderer,
    xml=XmlListRenderer,
    csv=CsvListRenderer,
    html=HtmlListRenderer,
    plain=PlainListRenderer,
    )

NOTE_KEYWORD = "_note"

class TaskCmd(object):
    def __init__(self):
        self.lastTaskId = None
        self.kFilters = [] # Permanent keyword filters (List of KeywordFilter)
        self.pFilter = ""  # Permanent project filter (name of project)
        for name in bugutils.PROPERTY_NAMES:
            dbutils.getOrCreateKeyword(name, interactive=False)
        dbutils.getOrCreateKeyword(NOTE_KEYWORD, interactive=False)

    def _t_add(self, cmd, line):
        """Code shared by t_add, bug_add and n_add."""
        line = line.strip()
        if not line:
            raise BadUsageException("Missing parameters")
        projectName, title, keywordDict = parseutils.parseLine(line)
        if not title:
            raise BadUsageException("Missing title")
        task = dbutils.addTask(projectName, title, keywordDict)
        if not task:
            tui.reinjectInRawInput(u"%s %s" % (cmd, line))
            return None
        self.lastTaskId = task.id
        return task

    def do_t_add(self, line):
        """Add new task. Will prompt to create keywords if they do not exist.
        t_add <projectName> [@<keyword1>] [@<keyword2>] <title>"""
        task = self._t_add("t_add", line)
        if task:
            print "Added task '%s' (id=%d)" % (task.title, task.id)
    complete_t_add = projectAndKeywordCompleter

    def do_bug_add(self, line):
        """Add a bug-type task. Will create a task and ask additional info.
        bug_add <project_name> [@<keyword1>] [@<keyword2>] <title>
        """
        task = self._t_add("bug_add", line)
        if not task:
            return

        keywordDict = task.getKeywordDict()
        bugutils.editBugKeywords(keywordDict)
        task.setKeywordDict(keywordDict)
        task.urgency = bugutils.computeUrgency(keywordDict)

        print "Added bug '%s' (id=%d, urgency=%d)" % (task.title, task.id, task.urgency)

    complete_bug_add = ProjectCompleter(1)

    def do_n_add(self, line):
        """Add a note. A note is a task with the @note keyword.
        n_add <project_name> [@<keyword1>] [@<keyword2>] <title>
        """
        task = self._t_add("n_add", line)
        if not task:
            return
        keywordDict = task.getKeywordDict()
        keywordDict[NOTE_KEYWORD] = None
        task.setKeywordDict(keywordDict)
        print "Added note '%s' (id=%d)" % (task.title, task.id)
    complete_n_add = projectAndKeywordCompleter

    def do_bug_edit(self, line):
        """Edit a bug.
        bug_edit <id>"""
        task = self._t_edit(line)
        if not task:
            return

        keywordDict = task.getKeywordDict()
        bugutils.editBugKeywords(keywordDict)
        task.setKeywordDict(keywordDict)
        task.urgency = bugutils.computeUrgency(keywordDict)
    complete_bug_edit = taskIdCompleter

    def getTaskFromId(self, line):
        line = line.strip()
        if line == '_':
            if self.lastTaskId is None:
                raise YokadiException("No previous task defined")
            line = str(self.lastTaskId)
        task = dbutils.getTaskFromId(line)
        if line != '_':
            self.lastTaskId = task.id
        return task

    def do_t_describe(self, line):
        """Starts an editor to enter a longer description of a task.
        t_describe <id>"""
        task = self.getTaskFromId(line)
        try:
            description = tui.editText(task.description)
        except Exception, e:
            raise YokadiException(e)
        task.description = description

    complete_t_describe = taskIdCompleter

    def do_t_set_urgency(self, line):
        """@deprecated: should be removed"""
        tui.warnDeprecated("t_set_urgency", "t_urgency")
        self.do_t_urgency(line)

    def do_t_urgency(self, line):
        """Defines urgency of a task.
        t_urgency <id> <value>"""

        tokens = parseutils.simplifySpaces(line).split(" ")
        if len(tokens) != 2:
            raise BadUsageException("You must provide a taskId and an urgency value")
        task = self.getTaskFromId(tokens[0])
        try:
            # Do not use isdigit(), so that we can set negative urgency. This
            # make it possible to stick tasks to the bottom of the list.
            urgency = int(tokens[1])
        except ValueError:
            raise BadUsageException("Task urgency must be a digit")

        if urgency > 100:
            tui.warning("Max urgency is 100")
            urgency = 100
        elif urgency < -99:
            tui.warning("Min urgency is -99")
            urgency = -99

        task.urgency = urgency

    complete_t_set_urgency = taskIdCompleter
    complete_t_urgency = taskIdCompleter

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
        task = self.getTaskFromId(line)
        if task.recurrence and status == "done":
            task.dueDate = task.recurrence.getNext(task.dueDate)
            print "Task '%s' next occurrence is scheduled at %s" % (task.title, task.dueDate)
            print "To *really* mark this task done and forget it, remove its recurrence first with t_recurs %s none" % task.id
        else:
            task.status = status
            if status == "done":
                task.doneDate = datetime.now()
            else:
                task.doneDate = None
            print "Task '%s' marked as %s" % (task.title, status)

    def do_t_apply(self, line):
        """Apply a command to several tasks.
        t_apply <id1>[,<id2>,[<id3>]...]] <command> <args>"""
        tokens = line.split(" ", 2)
        if len(tokens) < 2:
            raise BadUsageException("Give at least a task id and a command")
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
        task = self.getTaskFromId(' '.join(args))
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

    def parser_t_purge(self):
        parser = YokadiOptionParser()
        parser.set_usage("t_purge [options]")
        parser.set_description("Remove old done tasks from all projects.")
        parser.add_option("-f", "--force", dest="force", default=False, action="store_true",
                          help="Skip confirmation prompt")
        delay = int(Config.byName("PURGE_DELAY").value)
        parser.add_option("-d", "--delay", dest="delay", default=delay,
                          type="int", help="Delay (in days) after which done tasks are destroyed. Default is %d." % delay)
        return parser

    def do_t_purge(self, line):
        parser = self.parser_t_purge()
        options, args = parser.parse_args(line)
        filters = []
        filters.append(Task.q.status == "done")
        filters.append(Task.q.doneDate < (datetime.now() - timedelta(days=options.delay)))
        tasks = Task.select(AND(*filters))
        if tasks.count() == 0:
            print "No tasks need to be purged"
            return
        print "The following tasks will be removed:"
        print "\n".join(["%s: %s" % (task.id, task.title) for task in tasks])
        if options.force or tui.confirm("Do you really want to remove those tasks (this action cannot be undone)?"):
            Task.deleteMany(AND(*filters))
            print "Tasks deleted"
        else:
            print "Purge canceled"

    def parser_t_list(self):
        parser = YokadiOptionParser()
        parser.set_usage("t_list [options] <project_or_keyword_filter>")
        parser.set_description(
            "List tasks filtered by project and/or keywords. "
            "'%' can be used as a wildcard in the project name: "
            "to list projects starting with 'foo', use 'foo%'. "
            "Keyword filtering is achieved with '@'. Ex.: "
            "t_list @home, t_list @_bug=2394")

        parser.add_option("-a", "--all", dest="status",
                          action="store_const", const="all",
                          help="all tasks (done and to be done)")

        parser.add_option("--started", dest="status",
                          action="store_const", const="started",
                          help="only started tasks")

        rangeList = ["today", "thisweek", "thismonth", "all"]
        parser.add_option("-d", "--done", dest="done",
                          help="only done tasks. <range> must be one of %s" % ", ".join(rangeList),
                          metavar="<range>")

        parser.add_option("-u", "--urgency", dest="urgency",
                          type="int",
                          help="tasks with urgency greater or equal than <urgency>",
                          metavar="<urgency>")

        parser.add_option("-t", "--top-due", dest="topDue",
                          default=False, action="store_true",
                          help="top 5 urgent tasks of each project based on due date")

        parser.add_option("--overdue", dest="overdue",
                          default=False, action="store_true",
                          help="all overdue tasks")

        parser.add_option("-k", "--keyword", dest="keyword",
                          help="Group tasks by given keyword instead of project. The % wildcard can be used.",
                          metavar="<keyword>")

        parser.add_option("-s", "--search", dest="search",
                          action="append",
                          help="only list tasks whose title or description match <value>. You can repeat this option to search on multiple words.",
                          metavar="<value>")

        formatList = ["auto"] + gRendererClassDict.keys()
        parser.add_option("-f", "--format", dest="format",
                          type="choice", default="auto", choices=formatList,
                          help="how should the task list be formated. <format> can be %s" % ", ".join(formatList),
                          metavar="<format>")
        parser.add_option("-o", "--output", dest="output",
                          help="Output task list to <file>",
                          metavar="<file>")
        return parser

    def _parseListLine(self, parser, line):
        """
        Parse line with parser, returns a tuple of the form
        (options, projectList, filters)
        """
        options, args = parser.parse_args(line)
        if len(args) > 0:
            projectName, keywordFilters = parseutils.extractKeywords(u" ".join(args))
        else:
            projectName = ""
            keywordFilters = []

        if self.kFilters:
            # Add keyword filter
            keywordFilters.extend(self.kFilters)

        if not projectName:
            if self.pFilter:
                # If a project filter is defined, use it as none was provided
                projectName = self.pFilter
            else:
                # Take all project if none provided
                projectName = "%"

        if projectName.startswith("!"):
            projectName = projectName[1:]
            projectList = Project.select(NOT(LIKE(Project.q.name, projectName)))
        else:
            projectList = Project.select(LIKE(Project.q.name, projectName))

        if projectList.count() == 0:
            raise YokadiException("Found no project matching '%s'" % projectName)

        # Check keywords exist
        parseutils.warnIfKeywordDoesNotExist(keywordFilters)

        # Filtering and sorting according to parameters
        filters = []

        # Filter on keywords
        for keywordFilter in keywordFilters:
            filters.append(keywordFilter.filter())

        # Search
        if options.search:
            for word in options.search:
                filters.append(OR(LIKE(Task.q.title, "%" + word + "%"),
                                  LIKE(Task.q.description, "%" + word + "%")))

        return options, projectList, filters

    def _renderList(self, renderer, projectList, filters, order, limit, groupKeyword):
        """
        Render a list using renderer, according to the restrictions set by the
        other parameters
        """
        if groupKeyword:
            if groupKeyword.startswith("@"):
                groupKeyword = groupKeyword[1:]
            for keyword in Keyword.select(LIKE(Keyword.q.name, groupKeyword)):
                if unicode(keyword.name).startswith("_") and not groupKeyword.startswith("_"):
                    #BUG: cannot filter on db side because sqlobject does not understand ESCAPE needed whith _
                    continue
                taskList = Task.select(AND(TaskKeyword.q.keywordID == keyword.id,
                                           *filters),
                                       orderBy=order, limit=limit, distinct=True,
                                       join=LEFTJOINOn(Task, TaskKeyword, Task.q.id == TaskKeyword.q.taskID))
                taskList = list(taskList)
                if projectList:
                    taskList = [x for x in taskList if x.project in projectList]
                if len(taskList) > 0:
                    renderer.addTaskList(unicode(keyword), taskList)
            renderer.end()
        else:
            hiddenProjectNames = []
            for project in projectList:
                if not project.active:
                    hiddenProjectNames.append(project.name)
                    continue
                taskList = Task.select(AND(Task.q.projectID == project.id, *filters),
                                       orderBy=order, limit=limit, distinct=True,
                                       join=LEFTJOINOn(Task, TaskKeyword, Task.q.id == TaskKeyword.q.taskID))
                taskList = list(taskList)

                if len(taskList) > 0:
                    renderer.addTaskList(unicode(project), taskList)
            renderer.end()

            if len(hiddenProjectNames) > 0:
                tui.info("hidden projects: %s" % ", ".join(hiddenProjectNames))

    def do_t_list(self, line):

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
        options, projectList, filters = self._parseListLine(self.parser_t_list(), line)

        # Skip notes
        filters.append(parseutils.KeywordFilter("!@note").filter())

        # Handle t_list specific options
        order = -Task.q.urgency, Task.q.creationDate
        limit = None
        if options.done:
            filters.append(Task.q.status == 'done')
            if options.done != "all":
                filters.append(parseutils.createFilterFromRange(options.done))
        elif options.status == "all":
            pass
        elif options.status == "started":
            filters.append(Task.q.status == 'started')
        else:
            filters.append(Task.q.status != 'done')
        if options.urgency:
            order = -Task.q.urgency
            filters.append(Task.q.urgency >= options.urgency)
        if options.topDue:
            filters.append(Task.q.dueDate != None)
            order = Task.q.dueDate
            limit = 5
        if options.overdue:
            filters.append(Task.q.dueDate < datetime.now())
            order = Task.q.dueDate

        # Define output
        if options.output:
            out = open(options.output, "w")
        else:
            out = tui.stdout

        # Instantiate renderer
        rendererClass = selectRendererClass()
        renderer = rendererClass(out)

        # Fill the renderer
        self._renderList(renderer, projectList, filters, order, limit, options.keyword)
    complete_t_list = projectAndKeywordCompleter

    def parser_n_list(self):
        parser = YokadiOptionParser()
        parser.set_usage("n_list [options] <project_or_keyword_filter>")
        parser.set_description(
            "List notes filtered by project and/or keywords. "
            "'%' can be used as a wildcard in the project name: "
            "to list projects starting with 'foo', use 'foo%'. "
            "Keyword filtering is achieved with '@'. Ex.: "
            "n_list @home, n_list @_bug=2394")

        parser.add_option("-s", "--search", dest="search",
                          action="append",
                          help="only list notes whose title or description match <value>. You can repeat this option to search on multiple words.",
                          metavar="<value>")

        parser.add_option("-k", "--keyword", dest="keyword",
                          help="Group tasks by given keyword instead of project. The % wildcard can be used.",
                          metavar="<keyword>")
        return parser

    def do_n_list(self, line):
        options, projectList, filters = self._parseListLine(self.parser_n_list(), line)
        filters.append(parseutils.KeywordFilter("@note").filter())
        order = Task.q.creationDate
        renderer = TextListRenderer(tui.stdout)
        self._renderList(renderer, projectList, filters, order, limit=None, groupKeyword=options.keyword)
    complete_n_list = projectAndKeywordCompleter

    def do_t_reorder(self, line):
        """Reorder tasks of a project.
        It works by starting an editor with the task list: you can then change
        the order of the lines and save the list. The urgency field will be
        updated to match the order.
        t_reorder <project_name>"""
        project = Project.byName(line)
        taskList = Task.select(AND(Task.q.projectID == project.id,
                                   Task.q.status != 'done'),
                               orderBy= -Task.q.urgency)
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

        task = self.getTaskFromId(' '.join(args))

        if options.output in ("all", "summary"):
            keywordDict = task.getKeywordDict()
            keywordArray = []
            for name, value in keywordDict.items():
                txt = name
                if value:
                    txt += "=" + str(value)
                keywordArray.append(txt)
                keywordArray.sort()
            keywords = ", ".join(keywordArray)
            fields = [
                ("Project", task.project.name),
                ("Title", task.title),
                ("Created", task.creationDate),
                ("Due", task.dueDate),
                ("Status", task.status),
                ("Urgency", task.urgency),
                ("Recurrence", task.recurrence),
                ("Keywords", keywords),
                ]

            if task.status == "done":
                fields.append(("Done", task.doneDate))

            tui.renderFields(fields)

        if options.output in ("all", "description") and task.description:
            if options.output == "all":
                print
            print task.description

    complete_t_show = taskIdCompleter

    def _t_edit(self, line):
        """Code shared by t_edit and bug_edit."""
        def editComplete(text, state):
            """ Specific completer for the edit prompt.
            This subfunction should stay here because it needs to access to cmd members"""
            if state == 0:
                origline = readline.get_line_buffer()
                line = origline.lstrip()
                stripped = len(origline) - len(line)
                begidx = readline.get_begidx() - stripped
                endidx = readline.get_endidx() - stripped
                if begidx > 0:
                    self.completion_matches = projectAndKeywordCompleter("", text, line, begidx, endidx, shift=1)
                else:
                    self.completion_matches = []
            try:
                return self.completion_matches[state]
            except IndexError:
                return None

        task = self.getTaskFromId(line)

        # Create task line
        taskLine = parseutils.createLine("", task.title, task.getKeywordDict())

        oldCompleter = readline.get_completer() # Backup previous completer to restore it in the end
        readline.set_completer(editComplete)    # Switch to specific completer

        while True:
            # Edit
            print "(Press Ctrl+C to cancel)"
            try:
                line = tui.editLine(taskLine)
                if not line.strip():
                    tui.warning("Missing title")
                    continue
            except KeyboardInterrupt:
                print
                print "Cancelled"
                task = None
                break
            foo, title, keywordDict = parseutils.parseLine(task.project.name + " " + line)
            if dbutils.updateTask(task, task.project.name, title, keywordDict):
                break

        readline.set_completer(oldCompleter)   # Restore standard completer
        return task

    def do_t_edit(self, line):
        """Edit a task.
        t_edit <id>"""
        self._t_edit(line)
    complete_t_edit = taskIdCompleter

    def do_t_set_project(self, line):
        """@deprecated: should be removed"""
        tui.warnDeprecated("t_set_project", "t_project")
        self.do_t_project(line)


    def do_t_project(self, line):
        """Set task's project.
        t_project <id> <project>"""
        tokens = parseutils.simplifySpaces(line).split(" ")
        if len(tokens) != 2:
            raise YokadiException("You should give two arguments: <task id> <project>")
        task = self.getTaskFromId(tokens[0])
        projectName = tokens[1]

        task.project = dbutils.getOrCreateProject(projectName)
        if task.project:
            print "Moved task '%s' to project '%s'" % (task.title, projectName)

    complete_t_set_project = ProjectCompleter(2)
    complete_t_project = ProjectCompleter(2)

    def do_t_set_due(self, line):
        """@deprecated: should be removed"""
        tui.warnDeprecated("t_set_due", "t_due")
        self.do_t_due(line)

    def do_t_due(self, line):
        """Set task's due date
        t_due <id> <date>

        Date can be specified as a relative offset:
        - +5M: in 5 minutes
        - +3H: in 3 hours
        - +1D: in 1 day
        - +6W: in 6 weeks

        As a day in the week:
        - tomorrow:      tomorrow, same hour
        - tuesday 12:10: next tuesday, at 12:10
        - fr 15:30:      next friday, at 15:30

        Or as an absolute date or time:
        - 10:38:            at 10:38 today
        - 25/09/2010 12:10: on the 25th of September, 2010, at 12:10
        - 23/02/2010:       on the 23th of February, 2010
        - 01/04:            on the 1st of April
        - 12:               on the 12th of current month

        To reset a due date, use "none"."""
        line = parseutils.simplifySpaces(line)
        if len(line.split()) < 2:
            raise YokadiException("Give a task id and time, date or date & time")
        taskId, line = line.strip().split(" ", 1)
        task = self.getTaskFromId(taskId)

        if line.lower() == "none":
            task.dueDate = None
            print "Due date for task '%s' reset" % task.title
        else:
            task.dueDate = ydateutils.parseHumaneDateTime(line)
            print "Due date for task '%s' set to %s" % (task.title, task.dueDate.ctime())

    complete_t_set_due = dueDateCompleter
    complete_t_due = dueDateCompleter

    def do_t_add_keywords(self, line):
        """Add keywords to an existing task
        t_add_keyword <id> <@keyword1> <@keyword2>[=<value>]...
        """
        tokens = parseutils.simplifySpaces(line).split(" ", 1)
        if len(tokens) < 2:
            raise YokadiException("You should give at least two arguments: <task id> <keyword>")
        task = dbutils.getTaskFromId(tokens[0])
        garbage, keywordFilters = parseutils.extractKeywords(tokens[1])
        newKwDict = parseutils.keywordFiltersToDict(keywordFilters)
        if garbage:
            raise YokadiException("Cannot parse line, got garbage (%s). Maybe you forgot to add @ before keyword ?"
                                   % garbage)

        dbutils.createMissingKeywords(newKwDict.keys())

        kwDict = task.getKeywordDict()
        kwDict.update(newKwDict)
        task.setKeywordDict(kwDict)

    def do_t_recurs(self, line):
        """Make a task recurs
        t_recurs <id> yearly <dd/mm> <HH:MM>
        t_recurs <id> monthly <dd> <HH:MM>
        t_recurs <id> monthly <first/second/third/last> <mo, tu, we, th, fr, sa, su> <hh:mm>
        t_recurs <id> quarterly <dd> <HH:MM>
        t_recurs <id> quarterly <first/second/third/last> <mo, tu, we, th, fr, sa, su> <hh:mm>
        t_recurs <id> weekly <mo, tu, we, th, fr, sa, su> <hh:mm>
        t_recurs <id> daily <HH:MM>
        t_recurs <id> none (remove recurrence)"""
        tokens = parseutils.simplifySpaces(line).split()
        if len(tokens) < 2:
            raise YokadiException("You should give at least two arguments: <task id> <recurrence>")
        task = self.getTaskFromId(tokens[0])

        # Define recurrence:
        freq = byminute = byhour = byweekday = bymonthday = bymonth = None

        tokens[1] = tokens[1].lower()

        if tokens[1] == "none":
            if task.recurrence:
                task.recurrence.destroySelf()
                task.recurrence = None
            return
        elif tokens[1] == "daily":
            if len(tokens) != 3:
                raise YokadiException("You should give time for daily task")
            freq = rrule.DAILY
            byhour, byminute = ydateutils.getHourAndMinute(tokens[2])
        elif tokens[1] == "weekly":
            freq = rrule.WEEKLY
            if len(tokens) != 4:
                raise YokadiException("You should give day and time for weekly task")
            byweekday = ydateutils.getWeekDayNumberFromDay(tokens[2].lower())
            byhour, byminute = ydateutils.getHourAndMinute(tokens[3])
        elif tokens[1] in ("monthly", "quarterly"):
            if tokens[1] == "monthly":
                freq = rrule.MONTHLY
            else:
                # quarterly
                freq = rrule.YEARLY
                bymonth = [1, 4, 7, 10]
            if len(tokens) < 4:
                raise YokadiException("You should give day and time for %s task" % (tokens[1],))
            try:
                bymonthday = int(tokens[2])
                byhour, byminute = ydateutils.getHourAndMinute(tokens[3])
            except ValueError:
                POSITION = { "first" : 1, "second" : 2, "third" : 3, "fourth" : 4, "last" :-1 }
                if tokens[2].lower() in POSITION.keys() and len(tokens) == 5:
                    byweekday = rrule.weekday(ydateutils.getWeekDayNumberFromDay(tokens[3].lower()),
                                              POSITION[tokens[2]])
                    byhour, byminute = ydateutils.getHourAndMinute(tokens[4])
                    bymonthday = None # Default to current day number - need to be blanked                    
                else:
                    raise YokadiException("Unable to understand date. See help t_recurs for details")
        elif tokens[1] == "yearly":
            freq = rrule.YEARLY
            rDate = ydateutils.parseHumaneDateTime(" ".join(tokens[2:]))
            bymonth = rDate.month
            bymonthday = rDate.day
            byhour = rDate.hour
            byminute = rDate.minute
        else:
            raise YokadiException("Unknown frequency. Available: daily, weekly, monthly and yearly")

        if task.recurrence is None:
            task.recurrence = Recurrence()
        rr = rrule.rrule(freq, byhour=byhour, byminute=byminute, byweekday=byweekday,
                         bymonthday=bymonthday, bymonth=bymonth)
        task.recurrence.setRrule(rr)
        task.dueDate = task.recurrence.getNext()
    complete_t_recurs = recurrenceCompleter


    def do_t_filter(self, line):
        """Define permanent keyword filter used by t_list
        Ex.:
            - t_filter @work (filter all task that have the "work" keyword)
            - t_filter none (remove filter)"""
        #TODO: add completion

        if not line:
            raise YokadiException("You must give keyword as argument or 'none' to reset filter")

        if parseutils.simplifySpaces(line).lower() == "none":
            self.kFilters = []
            self.pFilter = ""
            self.prompt = "yokadi> "
        else:
            projectName, keywordFilters = parseutils.extractKeywords(line)
            self.kFilters = keywordFilters
            self.pFilter = projectName
            prompt = "y"
            if self.pFilter:
                prompt += " %s" % projectName
            if self.kFilters:
                parseutils.warnIfKeywordDoesNotExist(self.kFilters)
                prompt += " %s" % (" ".join([str(k) for k in keywordFilters]))
            self.prompt = "%s> " % prompt

# vi: ts=4 sw=4 et
