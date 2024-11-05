# -*- coding: UTF-8 -*-
"""
Task related commands.

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import os
import readline
import re
from datetime import datetime, timedelta
from sqlalchemy import or_, desc
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from yokadi.core.db import Keyword, Project, Task, TaskKeyword, NOTE_KEYWORD
from yokadi.core import bugutils
from yokadi.core import dbutils
from yokadi.core import db
from yokadi.core import ydateutils
from yokadi.core.recurrencerule import RecurrenceRule
from yokadi.ycli import massedit
from yokadi.ycli.basicparseutils import parseOneWordName
from yokadi.ycli import parseutils
from yokadi.ycli import tui
from yokadi.ycli.completers import ProjectCompleter, projectAndKeywordCompleter, \
    taskIdCompleter, recurrenceCompleter, dueDateCompleter
from yokadi.core.dbutils import DbFilter, KeywordFilter
from yokadi.core.yokadiexception import YokadiException, BadUsageException
from yokadi.ycli.textlistrenderer import TextListRenderer
from yokadi.ycli.xmllistrenderer import XmlListRenderer
from yokadi.ycli.csvlistrenderer import CsvListRenderer
from yokadi.ycli.htmllistrenderer import HtmlListRenderer
from yokadi.ycli.plainlistrenderer import PlainListRenderer
from yokadi.core.yokadioptionparser import YokadiOptionParser

gRendererClassDict = dict(
    text=TextListRenderer,
    xml=XmlListRenderer,
    csv=CsvListRenderer,
    html=HtmlListRenderer,
    plain=PlainListRenderer,
)


class TaskCmd(object):
    def __init__(self):
        self.lastTaskId = None  # Last id created, used
        self.lastProjectName = None  # Last project name used
        self.lastTaskIds = []  # Last list of ids selected with t_list
        self.kFilters = []  # Permanent keyword filters (List of KeywordFilter)
        self.pFilter = ""  # Permanent project filter (name of project)
        self.session = db.getSession()
        for name in bugutils.PROPERTY_NAMES:
            dbutils.getOrCreateKeyword(name, interactive=False)
        dbutils.getOrCreateKeyword(NOTE_KEYWORD, interactive=False)
        self.session.commit()

    def _parser_t_add(self, cmd):
        """Code shared by t_add, bug_add and n_add parsers."""
        parser = YokadiOptionParser()
        parser.usage = "%s [options] <projectName> [@<keyword1>] [@<keyword2>] <title>" % cmd
        parser.description = "Add new %s. Will prompt to create keywords if they do not exist." % cmd
        parser.add_argument("-d", "--describe", dest="describe", default=False, action="store_true",
                            help="Directly open editor to describe task")
        parser.add_argument('cmd', nargs='*')
        return parser

    def _t_add(self, cmd, line):
        """Code shared by t_add, bug_add and n_add."""
        parser = self._parser_t_add(cmd)
        args = parser.parse_args(line)

        line = " ".join(args.cmd)
        if not line:
            raise BadUsageException("Missing parameters")
        projectName, title, keywordDict = parseutils.parseLine(line)
        projectName = self._realProjectName(projectName)
        if not title:
            raise BadUsageException("Missing title")

        task = dbutils.addTask(projectName, title, keywordDict)
        if not task:
            tui.reinjectInRawInput("%s %s" % (cmd, line))
            return None
        self.lastTaskId = task.id

        if args.describe:
            self.do_t_describe(self.lastTaskId)
        return task

    def do_t_add(self, line):
        """Add new task. Will prompt to create keywords if they do not exist.
        t_add <projectName> [@<keyword1>] [@<keyword2>] <title>"""
        task = self._t_add("t_add", line)
        if task:
            self.session.add(task)
            self.session.commit()
            print("Added task '%s' (id=%d)" % (task.title, task.id))

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

        self.session.add(task)
        self.session.commit()
        print("Added bug '%s' (id=%d, urgency=%d)" % (task.title, task.id, task.urgency))

    complete_bug_add = ProjectCompleter(1)

    def do_n_add(self, line):
        """Add a note. A note is a task with the @_note keyword.
        n_add <project_name> [@<keyword1>] [@<keyword2>] <title>
        """
        task = self._t_add("n_add", line)
        if not task:
            return
        self.session.add(task)
        keywordDict = task.getKeywordDict()
        keywordDict[NOTE_KEYWORD] = None
        task.setKeywordDict(keywordDict)
        self.session.commit()
        print("Added note '%s' (id=%d)" % (task.title, task.id))
    complete_n_add = projectAndKeywordCompleter

    def do_bug_edit(self, line):
        """Edit a bug.
        bug_edit <id>"""
        task = self._t_edit(line, keywordEditor=bugutils.editBugKeywords)
        if task:
            self.session.commit()
    complete_bug_edit = taskIdCompleter

    def getTaskFromId(self, tid):
        if tid == '_':
            if self.lastTaskId is None:
                raise YokadiException("No previous task defined")
            tid = self.lastTaskId
        task = dbutils.getTaskFromId(tid)
        if tid != '_':
            self.lastTaskId = task.id
        return task

    def do_t_describe(self, line):
        """Starts an editor to enter a longer description of a task.
        t_describe <id>"""
        def updateDescription(description):
            task.description = description

        task = self.getTaskFromId(line)
        try:
            description = tui.editText(task.description,
                                       onChanged=updateDescription,
                                       lockManager=dbutils.TaskLockManager(task),
                                       prefix="yokadi-%s-%s-" % (task.project, task.title))
        except Exception as e:
            raise YokadiException(e)
        updateDescription(description)
        self.session.commit()

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
        self.session.commit()

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
        task.setStatus(status)
        self.session.commit()
        if task.recurrence and status == "done":
            print("Task '%s' next occurrence is scheduled at %s" % (task.title, task.dueDate))
            print("To *really* mark this task done and forget it, remove its recurrence first"
                  " with t_recurs %s none" % task.id)
        else:
            print("Task '%s' marked as %s" % (task.title, status))

    def do_t_apply(self, line):
        """Apply a command to several tasks.
        t_apply <id1>[,<id2>,[<id3>]...]] <command> <args>
        Use x-y to select task range from x to y
        Use __ to select all tasks previously selected with t_list"""
        ids = []
        if "__" in line:
            if self.lastTaskIds:
                line = line.replace("__", ",".join([str(i) for i in self.lastTaskIds]))
            else:
                raise BadUsageException("You must select tasks with t_list prior to use __")
        rangeId = re.compile(r"(\d+)-(\d+)")
        tokens = re.split(r"[\s|,]", line)
        if len(tokens) < 2:
            raise BadUsageException("Give at least a task id and a command")

        idScan = True  # Indicate we are parsing ids
        cmdTokens = []  # Command that we want to apply
        for token in tokens:
            if token == "":
                continue
            if idScan:
                result = rangeId.match(token)
                if result:
                    ids.extend(list(range(int(result.group(1)), int(result.group(2)) + 1)))
                elif token.isdigit():
                    ids.append(int(token))
                else:
                    # Id list is finished. Grab rest of line.
                    cmdTokens.append(token)
                    idScan = False
            else:
                cmdTokens.append(token)

        if not cmdTokens:
            raise BadUsageException("Give a command to apply")
        cmd = cmdTokens.pop(0)
        for taskId in ids:
            line = " ".join([cmd, str(taskId), " ".join(cmdTokens)])
            print("Executing: %s" % line)
            self.onecmd(line.strip())

    complete_t_apply = taskIdCompleter

    def parser_t_remove(self):
        parser = YokadiOptionParser()
        parser.usage = "t_remove [options] <id>"
        parser.description = "Delete a task."
        parser.add_argument("-f", dest="force", default=False, action="store_true",
                            help="Skip confirmation prompt")
        parser.add_argument("id")
        return parser

    def do_t_remove(self, line):
        parser = self.parser_t_remove()
        args = parser.parse_args(line)
        task = self.getTaskFromId(args.id)
        if not args.force:
            if not tui.confirm("Remove task '%s'" % task.title):
                return
        project = task.project
        self.session.delete(task)
        print("Task '%s' removed" % (task.title))

        # Delete project with no associated tasks
        if self.session.query(Task).filter_by(project=project).count() == 0:
            self.session.delete(project)
        self.session.commit()
    complete_t_remove = taskIdCompleter

    def parser_t_purge(self):
        parser = YokadiOptionParser()
        parser.usage = "t_purge [options]"
        parser.description = "Remove old done tasks from all projects."
        parser.add_argument("-f", "--force", dest="force", default=False, action="store_true",
                            help="Skip confirmation prompt")
        delay = int(db.getConfigKey("PURGE_DELAY", environ=False))
        parser.add_argument("-d", "--delay", dest="delay", default=delay,
                            type=int, help="Delay (in days) after which done tasks are destroyed."
                                           " Default is %d." % delay)
        return parser

    def do_t_purge(self, line):
        parser = self.parser_t_purge()
        args = parser.parse_args(line)
        filters = []
        filters.append(Task.status == "done")
        filters.append(Task.doneDate < (datetime.now() - timedelta(days=args.delay)))
        tasks = self.session.query(Task).filter(*filters)
        if tasks.count() == 0:
            print("No tasks need to be purged")
            return
        print("The following tasks will be removed:")
        print("\n".join(["%s: %s" % (task.id, task.title) for task in tasks]))
        if args.force or tui.confirm("Do you really want to remove those tasks (this action cannot be undone)?"):
            self.session.delete(tasks)
            self.session.commit()
            print("Tasks deleted")
        else:
            print("Purge canceled")

    def parser_t_list(self):
        parser = YokadiOptionParser()
        parser.usage = "t_list [options] <project_or_keyword_filter>"
        parser.description = "List tasks filtered by project and/or keywords. " \
                             "'%' can be used as a wildcard in the project name: " \
                             "to list projects starting with 'foo', use 'foo%'. " \
                             "Keyword filtering is achieved with '@'. Ex.: " \
                             "t_list @home, t_list @_bug=2394"

        parser.add_argument("-a", "--all", dest="status",
                            action="store_const", const="all",
                            help="all tasks (done and to be done)")

        parser.add_argument("--started", dest="status",
                            action="store_const", const="started",
                            help="only started tasks")

        rangeList = ["today", "thisweek", "thismonth", "all"]
        parser.add_argument("-d", "--done", dest="done",
                            help="only done tasks. <range> must be either one of %s or a date using the same format"
                                 " as t_due" % ", ".join(rangeList),
                            metavar="<range>")

        parser.add_argument("-u", "--urgency", dest="urgency",
                            type=int,
                            help="tasks with urgency greater or equal than <urgency>",
                            metavar="<urgency>")

        parser.add_argument("-t", "--top-due", dest="topDue",
                            default=False, action="store_true",
                            help="top 5 urgent tasks of each project based on due date")

        parser.add_argument("--overdue", dest="due",
                            action="append_const", const="now",
                            help="all overdue tasks")

        parser.add_argument("--due", dest="due",
                            action="append",
                            help="""only list tasks due before/after <limit>. <limit> is a
                            date optionaly prefixed with a comparison operator.
                            Valid operators are: <, <=, >=, and >.
                            Example of valid limits:

                            - tomorrow: due date <= tomorrow, 23:59:59
                            - today: due date <= today, 23:59:59
                            - >today: due date > today: 23:59:59
                            """,
                            metavar="<limit>")

        parser.add_argument("-k", "--keyword", dest="keyword",
                            help="Group tasks by given keyword instead of project. The %% wildcard can be used.",
                            metavar="<keyword>")

        parser.add_argument("-s", "--search", dest="search",
                            action="append",
                            help="only list tasks whose title or description match <value>. You can repeat this"
                                 " option to search on multiple words.",
                            metavar="<value>")

        formatList = ["auto"] + list(gRendererClassDict.keys())
        parser.add_argument("-f", "--format", dest="format",
                            default="auto", choices=formatList,
                            help="how should the task list be formated. <format> can be %s" % ", ".join(formatList),
                            metavar="<format>")
        parser.add_argument("-o", "--output", dest="output",
                            help="Output task list to <file>",
                            metavar="<file>")

        parser.add_argument("filter", nargs="*", metavar="<project_or_keyword_filter>")

        return parser

    def _realProjectName(self, name):
        if name == '_':
            if self.lastProjectName is None:
                raise YokadiException("No previous project used")
        else:
            self.lastProjectName = name
        return self.lastProjectName

    def _parseListLine(self, parser, line):
        """
        Parse line with parser, returns a tuple of the form
        (options, projectList, filters)
        """
        args = parser.parse_args(line)
        if len(args.filter) > 0:
            projectName, filters = parseutils.extractKeywords(" ".join(args.filter))
        else:
            projectName = ""
            filters = []

        if self.kFilters:
            # Add keyword filter
            filters.extend(self.kFilters)

        if not projectName:
            if self.pFilter:
                # If a project filter is defined, use it as none was provided
                projectName = self.pFilter
            else:
                # Take all project if none provided
                projectName = "%"

        if projectName.startswith("!"):
            projectName = self._realProjectName(projectName[1:])
            projectList = self.session.query(Project).filter(Project.name.notlike(projectName)).all()
        else:
            projectName = self._realProjectName(projectName)
            projectList = self.session.query(Project).filter(Project.name.like(projectName)).all()

        if len(projectList) == 0:
            raise YokadiException("Found no project matching '%s'" % projectName)

        # Check keywords exist
        parseutils.warnIfKeywordDoesNotExist(filters)

        # Search
        if args.search:
            for word in args.search:
                if word.startswith("@"):
                    tui.warning("Maybe you want keyword search (without -s option) "
                                "instead of plain text search?")
                condition = or_(Task.title.like("%" + word + "%"),
                                Task.description.like("%" + word + "%"))
                filters.append(DbFilter(condition))

        return args, projectList, filters

    def _renderList(self, renderer, projectList, filters, order,
                    limit=None, groupKeyword=None):
        """
        Render a list using renderer, according to the restrictions set by the
        other parameters
        @param renderer: renderer class (for example: TextListRenderer)
        @param projectList: list of project name (as unicode string)
        @param filters: filters in sql alchemy format (example: Task.status == 'done')
        @param order: ordering in sqlalchemy format (example: desc(Task.urgency))
        @param limit: limit number tasks (int) or None for no limit
        @param groupKeyword: keyword used for grouping (as unicode string) or None
        """
        def applyFilters(lst):
            for filter in filters:
                lst = filter.apply(lst)
            return lst

        if groupKeyword:
            if groupKeyword.startswith("@"):
                groupKeyword = groupKeyword[1:]
            keywords = self.session.query(Keyword).filter(Keyword.name.like(groupKeyword))

            for keyword in sorted(keywords, key=lambda x: x.name.lower()):
                if str(keyword.name).startswith("_") and not groupKeyword.startswith("_"):
                    # BUG: cannot filter on db side because sqlobject does not
                    # understand ESCAPE needed with _. Need to test it with
                    # sqlalchemy
                    continue
                taskList = self.session.query(Task).filter(TaskKeyword.keywordId == keyword.id)
                taskList = taskList.outerjoin(TaskKeyword, Task.taskKeywords)
                taskList = applyFilters(taskList)
                taskList = taskList.order_by(*order).limit(limit).distinct()
                taskList = list(taskList)
                if projectList:
                    taskList = [x for x in taskList if x.project in projectList]
                if len(taskList) > 0:
                    self.lastTaskIds.extend([t.id for t in taskList])  # Keep selected id for further use
                    renderer.addTaskList(str(keyword), taskList)
            renderer.end()
        else:
            hiddenProjectNames = []
            for project in sorted(projectList, key=lambda x: x.name.lower()):
                if not project.active:
                    hiddenProjectNames.append(project.name)
                    continue
                taskList = self.session.query(Task).filter(Task.project == project)
                taskList = taskList.outerjoin(TaskKeyword, Task.taskKeywords)
                taskList = applyFilters(taskList)
                taskList = taskList.order_by(*order).limit(limit).distinct()
                taskList = list(taskList)
                if len(taskList) > 0:
                    self.lastTaskIds.extend([t.id for t in taskList])  # Keep selected id for further use
                    renderer.addTaskList(str(project), taskList)
            renderer.end()

            if len(hiddenProjectNames) > 0:
                tui.info("hidden projects: %s" % ", ".join(hiddenProjectNames))

    def do_t_list(self, line, renderer=None):

        def selectRendererClass():
            if args.format != "auto":
                return gRendererClassDict[args.format]

            defaultRendererClass = TextListRenderer
            if not args.output:
                return defaultRendererClass

            ext = os.path.splitext(args.output)[1]
            if not ext:
                return defaultRendererClass

            return gRendererClassDict.get(ext[1:], defaultRendererClass)

        # Reset last tasks id list
        self.lastTaskIds = []

        # BUG: completion based on parameter position is broken when parameter is given"
        args, projectList, filters = self._parseListLine(self.parser_t_list(), line)

        # Skip notes
        filters.append(KeywordFilter(NOTE_KEYWORD, negative=True))

        # Handle t_list specific options
        order = [desc(Task.urgency), Task.creationDate]
        limit = None
        if args.done:
            filters.append(DbFilter(Task.status == 'done'))
            if args.done != "all":
                minDate = ydateutils.parseMinDate(args.done)
                filters.append(DbFilter(Task.doneDate >= minDate))
        elif args.status == "all":
            pass
        elif args.status == "started":
            filters.append(DbFilter(Task.status == "started"))
        else:
            filters.append(DbFilter(Task.status != "done"))
        if args.urgency is not None:
            order = [desc(Task.urgency), ]
            filters.append(DbFilter(Task.urgency >= args.urgency))
        if args.topDue:
            filters.append(DbFilter(Task.dueDate is not None))
            order = [Task.dueDate, ]
            limit = 5
        if args.due:
            for due in args.due:
                dueOperator, dueLimit = ydateutils.parseDateLimit(due)
                filters.append(DbFilter(dueOperator(Task.dueDate, dueLimit)))
            order = [Task.dueDate, ]

        # Define output
        if args.output:
            out = open(args.output, "w", encoding='utf-8')
        else:
            out = tui.stdout

        # Instantiate renderer
        if renderer is None:
            rendererClass = selectRendererClass()
            renderer = rendererClass(out)

        # Fill the renderer
        self._renderList(renderer, projectList, filters, order, limit, args.keyword)
    complete_t_list = projectAndKeywordCompleter

    def parser_n_list(self):
        parser = YokadiOptionParser()
        parser.usage = "n_list [options] <project_or_keyword_filter>"
        parser.description = "List notes filtered by project and/or keywords. " \
            "'%' can be used as a wildcard in the project name: " \
            "to list projects starting with 'foo', use 'foo%'. " \
            "Keyword filtering is achieved with '@'. Ex.: " \
            "n_list @home, n_list @_bug=2394"

        parser.add_argument("-s", "--search", dest="search",
                            action="append",
                            help="only list notes whose title or description match <value>."
                                 " You can repeat this option to search on multiple words.",
                            metavar="<value>")

        parser.add_argument("-k", "--keyword", dest="keyword",
                            help="Group tasks by given keyword instead of project. The '%%' wildcard can be used.",
                            metavar="<keyword>")
        parser.add_argument("filter", nargs="*", metavar="<project_or_keyword_filter>")

        return parser

    def do_n_list(self, line):
        args, projectList, filters = self._parseListLine(self.parser_n_list(), line)

        filters.append(KeywordFilter(NOTE_KEYWORD))
        order = [Task.creationDate, ]
        renderer = TextListRenderer(tui.stdout, renderAsNotes=True)
        self._renderList(renderer, projectList, filters, order, limit=None,
                         groupKeyword=args.keyword)
    complete_n_list = projectAndKeywordCompleter

    def do_t_reorder(self, line):
        """Reorder tasks of a project.
        It works by starting an editor with the task list: you can then change
        the order of the lines and save the list. The urgency field will be
        updated to match the order.
        t_reorder <project_name>"""
        try:
            project = self.session.query(Project).filter_by(name=line).one()
        except (MultipleResultsFound, NoResultFound):
            raise BadUsageException("You must provide a valid project name")

        taskList = self.session.query(Task).filter(Task.projectId == project.id,
                                                   Task.status != 'done').order_by(desc(Task.urgency))
        lines = ["%d,%s" % (x.id, x.title) for x in taskList]
        text = tui.editText("\n".join(lines))

        ids = []
        for line in text.split("\n"):
            line = line.strip()
            if "," not in line:
                continue
            ids.append(int(line.split(",")[0]))

        ids.reverse()
        for urgency, taskId in enumerate(ids):
            task = self.session.get(Task, taskId)
            task.urgency = urgency
        self.session.commit()
    complete_t_reorder = ProjectCompleter(1)

    def do_t_medit(self, line):
        """Mass edit tasks of a project.
        t_medit <project_name>

        Starts a text editor with the task list, you can then:
        - edit tasks text and keywords
        - mark tasks as done or started
        - add new tasks
        - adjust urgency
        - delete tasks
        """
        if not line:
            raise BadUsageException("Missing parameters")
        projectName = parseOneWordName(line)
        projectName = self._realProjectName(projectName)
        project = dbutils.getOrCreateProject(projectName)
        if not project:
            return

        oldList = massedit.createEntriesForProject(project)
        oldText = massedit.createMEditText(oldList)
        newText = oldText
        while True:
            newText = tui.editText(newText, suffix=".medit")
            if newText == oldText:
                print("No changes")
                return

            try:
                newList = massedit.parseMEditText(newText)
            except massedit.ParseError as exc:
                print(exc)
                print()
                if tui.confirm("Modify text and try again"):
                    lst = newText.splitlines()
                    lst.insert(exc.lineNumber, "# ^ " + exc.message)
                    newText = "\n".join(lst)
                    continue
                else:
                    return

            try:
                massedit.applyChanges(project, oldList, newList)
                self.session.commit()
                break
            except YokadiException as exc:
                print(exc)
                print()
                if not tui.confirm("Modify text and try again"):
                    return
    complete_t_medit = ProjectCompleter(1)

    def parser_t_show(self):
        parser = YokadiOptionParser()
        parser.usage = "t_show [options] <id>"
        parser.description = "Display details of a task."
        choices = ["all", "summary", "description"]
        parser.add_argument("--output", dest="output",
                            choices=choices,
                            default="all",
                            help="<output> can be one of %s. If not set, it defaults to all." % ", ".join(choices),
                            metavar="<output>")
        parser.add_argument("id")
        return parser

    def do_t_show(self, line):
        parser = self.parser_t_show()
        args = parser.parse_args(line)

        task = self.getTaskFromId(args.id)

        if args.output in ("all", "summary"):
            keywordDict = task.getKeywordDict()
            keywordArray = []
            for name, value in list(keywordDict.items()):
                txt = name
                if value:
                    txt += "=" + str(value)
                keywordArray.append(txt)
                keywordArray.sort()
            keywords = ", ".join(keywordArray)

            if task.recurrence:
                recurrence = "{} (next: {})".format(
                    task.recurrence.getFrequencyAsString(),
                    task.recurrence.getNext()
                )
            else:
                recurrence = "None"

            fields = [
                ("Project", task.project.name),
                ("Title", task.title),
                ("ID", task.id),
                ("Created", task.creationDate),
                ("Due", task.dueDate),
                ("Status", task.status),
                ("Urgency", task.urgency),
                ("Recurrence", recurrence),
                ("Keywords", keywords),
            ]

            if task.status == "done":
                fields.append(("Done", task.doneDate))

            tui.renderFields(fields)

        if args.output in ("all", "description") and task.description:
            if args.output == "all":
                print()
            print(task.description)

    complete_t_show = taskIdCompleter

    def _t_edit(self, line, keywordEditor=None):
        """Code shared by t_edit and bug_edit.
        if keywordEditor is not None it will be called after editing the task.
        Returns the modified task if OK, None if cancelled"""
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
        keywordDict = task.getKeywordDict()
        userKeywordDict, keywordDict = dbutils.splitKeywordDict(keywordDict)
        taskLine = parseutils.createLine("", task.title, userKeywordDict)

        oldCompleter = readline.get_completer()  # Backup previous completer to restore it in the end
        readline.set_completer(editComplete)  # Switch to specific completer

        # Edit
        try:
            while True:
                print("(Press Ctrl+C to cancel)")
                try:
                    line = tui.editLine(taskLine)
                    if not line.strip():
                        tui.warning("Missing title")
                        continue
                except KeyboardInterrupt:
                    print()
                    print("Cancelled")
                    return None
                _, title, userKeywordDict = parseutils.parseLine(task.project.name + " " + line)

                if dbutils.createMissingKeywords(userKeywordDict.keys()):
                    # We were able to create missing keywords if there were any,
                    # we can now exit the edit loop
                    break
        finally:
            readline.set_completer(oldCompleter)

        keywordDict.update(userKeywordDict)
        if keywordEditor:
            keywordEditor(keywordDict)

        task.title = title
        task.setKeywordDict(keywordDict)
        return task

    def do_t_edit(self, line):
        """Edit a task.
        t_edit <id>"""
        self._t_edit(line)
        self.session.commit()
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
        projectName = tokens[1]
        projectName = self._realProjectName(projectName)
        project = dbutils.getOrCreateProject(projectName)
        if not project:
            return

        task = self.getTaskFromId(tokens[0])
        task.project = project
        self.session.commit()
        if task.project:
            print("Moved task '%s' to project '%s'" % (task.title, projectName))

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
            print("Due date for task '%s' reset" % task.title)
        else:
            task.dueDate = ydateutils.parseHumaneDateTime(line)
            print("Due date for task '%s' set to %s" % (task.title, task.dueDate.ctime()))
        self.session.commit()
    complete_t_set_due = dueDateCompleter
    complete_t_due = dueDateCompleter

    def do_t_add_keywords(self, line):
        """Add keywords to an existing task
        t_add_keywords <id> <@keyword1> <@keyword2>[=<value>]...
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

        if not dbutils.createMissingKeywords(list(newKwDict.keys())):
            # User cancel keyword creation
            return

        kwDict = task.getKeywordDict()
        kwDict.update(newKwDict)
        task.setKeywordDict(kwDict)
        self.session.commit()

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
        tokens = parseutils.simplifySpaces(line).split(" ", 1)
        if len(tokens) < 2:
            raise YokadiException("You should give at least two arguments: <task id> <recurrence>")
        task = self.getTaskFromId(tokens[0])
        rule = RecurrenceRule.fromHumaneString(tokens[1])
        task.setRecurrenceRule(rule)
        self.session.commit()
    complete_t_recurs = recurrenceCompleter

    def do_t_filter(self, line):
        """Define permanent keyword filter used by t_list
        Ex.:
            - t_filter @work (filter all task that have the "work" keyword)
            - t_filter none (remove filter)"""
        # TODO: add completion

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

    def do_t_to_note(self, line):
        """Turns a task into a note
        """
        task = self.getTaskFromId(line)
        task.toNote(self.session)
        self.session.commit()

    def do_n_to_task(self, line):
        """Turns a note into a task
        """
        task = self.getTaskFromId(line)
        task.toTask(self.session)
        self.session.commit()

# vi: ts=4 sw=4 et
