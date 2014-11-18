# -*- coding: UTF-8 -*-
"""
Task related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import os
import readline
import re
from datetime import datetime, timedelta
from dateutil import rrule
from sqlalchemy import or_, and_, desc
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from yokadi.core.db import Keyword, Project, Task, TaskKeyword, Recurrence
from yokadi.core import bugutils
from yokadi.core import dbutils
from yokadi.core import db
from yokadi.core import ydateutils
from yokadi.ycli import parseutils
from yokadi.ycli import tui
from yokadi.ycli.completers import ProjectCompleter, projectAndKeywordCompleter, \
                       taskIdCompleter, recurrenceCompleter, dueDateCompleter
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

NOTE_KEYWORD = "_note"


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
        parser.add_argument("-c", dest="crypt", default=False, action="store_true",
                          help="Encrypt title")
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

        if args.crypt:
            # Obfuscate line in history
            length = readline.get_current_history_length()
            if length > 0:  # Ensure history is positive to avoid crash with bad readline setup
                readline.replace_history_item(length - 1, "%s %s " % (cmd,
                                                                  line.replace(title, "<...encrypted...>")))
            # Encrypt title
            title = self.cryptoMgr.encrypt(title)

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
            if self.cryptoMgr.isEncrypted(task.title):
                title = "<... encrypted data...>"
            else:
                title = task.title
            self.session.add(task)
            self.session.commit()
            print("Added task '%s' (id=%d)" % (title, task.id))

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

        if self.cryptoMgr.isEncrypted(task.title):
            title = "<... encrypted data...>"
        else:
            title = task.title

        self.session.add(task)
        self.session.commit()
        print("Added bug '%s' (id=%d, urgency=%d)" % (title, task.id, task.urgency))

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
        if self.cryptoMgr.isEncrypted(task.title):
            title = "<... encrypted data...>"
        else:
            title = task.title
        self.session.commit()
        print("Added note '%s' (id=%d)" % (title, task.id))
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
        self.session.merge(task)
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
            if self.cryptoMgr.isEncrypted(task.title):
                task.description = self.cryptoMgr.encrypt(description)
            else:
                task.description = description

        task = self.getTaskFromId(line)
        try:
            if self.cryptoMgr.isEncrypted(task.title):
                # As title is encrypted, we assume description will be encrypted as well
                self.cryptoMgr.force_decrypt = True  # Decryption must be turned on to edit

            description = tui.editText(self.cryptoMgr.decrypt(task.description),
                                       onChanged=updateDescription,
                                       lockManager=dbutils.TaskLockManager(task),
                                       prefix="yokadi-%s-%s-" % (task.project, task.title))
        except Exception as e:
            raise YokadiException(e)
        updateDescription(description)
        self.session.merge(task)
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
        self.session.merge(task)
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
        if task.recurrence and status == "done":
            task.dueDate = task.recurrence.getNext(task.dueDate)
            print("Task '%s' next occurrence is scheduled at %s" % (task.title, task.dueDate))
            print("To *really* mark this task done and forget it, remove its recurrence first with t_recurs %s none" % task.id)
        else:
            task.status = status
            if status == "done":
                task.doneDate = datetime.now().replace(second=0, microsecond=0)
            else:
                task.doneDate = None
            print("Task '%s' marked as %s" % (task.title, status))
        self.session.merge(task)
        self.session.commit()

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
        rangeId = re.compile("(\d+)-(\d+)")
        tokens = re.split("[\s|,]", line)
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
                          type=int, help="Delay (in days) after which done tasks are destroyed. Default is %d." % delay)
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
                          help="only done tasks. <range> must be either one of %s or a date using the same format as t_due" % ", ".join(rangeList),
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
                          help="only list tasks whose title or description match <value>. You can repeat this option to search on multiple words.",
                          metavar="<value>")

        formatList = ["auto"] + list(gRendererClassDict.keys())
        parser.add_argument("-f", "--format", dest="format",
                          default="auto", choices=formatList,
                          help="how should the task list be formated. <format> can be %s" % ", ".join(formatList),
                          metavar="<format>")
        parser.add_argument("-o", "--output", dest="output",
                          help="Output task list to <file>",
                          metavar="<file>")
        parser.add_argument("--decrypt", dest="decrypt", default=False, action="store_true",
                          help="Decrypt task title and description")

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
            projectName, keywordFilters = parseutils.extractKeywords(" ".join(args.filter))
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
            projectName = self._realProjectName(projectName[1:])
            projectList = self.session.query(Project).filter(Project.name.notlike(projectName)).all()
        else:
            projectName = self._realProjectName(projectName)
            projectList = self.session.query(Project).filter(Project.name.like(projectName)).all()

        if len(projectList) == 0:
            raise YokadiException("Found no project matching '%s'" % projectName)

        # Check keywords exist
        parseutils.warnIfKeywordDoesNotExist(keywordFilters)

        # Filtering and sorting according to parameters
        filters = []

        # Filter on keywords
        for keywordFilter in keywordFilters:
            filters.append(keywordFilter.filter())

        # Search
        if args.search:
            for word in args.search:
                if word.startswith("@"):
                    tui.warning("Maybe you want keyword search (without -s option) "
                                "instead of plain text search?")
                filters.append(or_(Task.title.like("%" + word + "%"),
                                   Task.description.like("%" + word + "%")))

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
        if groupKeyword:
            if groupKeyword.startswith("@"):
                groupKeyword = groupKeyword[1:]
            for keyword in self.session.query(Keyword).filter(Keyword.name.like(groupKeyword)):
                if str(keyword.name).startswith("_") and not groupKeyword.startswith("_"):
                    # BUG: cannot filter on db side because sqlobject does not understand ESCAPE needed with _. Need to test it with sqlalchemy
                    continue
                taskList = self.session.query(Task).filter(TaskKeyword.keywordId == keyword.id).filter(and_(*filters))
                taskList = taskList.outerjoin(TaskKeyword, Task.taskKeywords)
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
            for project in projectList:
                if not project.active:
                    hiddenProjectNames.append(project.name)
                    continue
                taskList = self.session.query(Task).filter(Task.project == project).filter(and_(*filters))
                taskList = taskList.outerjoin(TaskKeyword, Task.taskKeywords)
                taskList = taskList.order_by(*order).limit(limit).distinct()
                taskList = list(taskList)
                if len(taskList) > 0:
                    self.lastTaskIds.extend([t.id for t in taskList])  # Keep selected id for further use
                    renderer.addTaskList(str(project), taskList)
            renderer.end()

            if len(hiddenProjectNames) > 0:
                tui.info("hidden projects: %s" % ", ".join(hiddenProjectNames))

    def do_t_list(self, line):

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
        filters.append(parseutils.KeywordFilter("!@" + NOTE_KEYWORD).filter())

        # Handle t_list specific options
        order = [desc(Task.urgency), Task.creationDate]
        limit = None
        if args.done:
            filters.append(Task.status == 'done')
            if args.done != "all":
                minDate = ydateutils.parseMinDate(args.done)
                filters.append(Task.doneDate >= minDate)
        elif args.status == "all":
            pass
        elif args.status == "started":
            filters.append(Task.status == "started")
        else:
            filters.append(Task.status != "done")
        if args.urgency:
            order = [desc(Task.urgency), ]
            filters.append(Task.urgency >= args.urgency)
        if args.topDue:
            filters.append(Task.dueDate != None)
            order = [Task.dueDate, ]
            limit = 5
        if args.due:
            for due in args.due:
                dueOperator, dueLimit = ydateutils.parseDateLimit(due)
                filters.append(dueOperator(Task.dueDate, dueLimit))
            order = [Task.dueDate, ]
        if args.decrypt:
            self.cryptoMgr.force_decrypt = True

        # Define output
        if args.output:
            out = open(args.output, "w", encoding='utf-8')
        else:
            out = tui.stdout

        # Instantiate renderer
        rendererClass = selectRendererClass()
        renderer = rendererClass(out, cryptoMgr=self.cryptoMgr)

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
                          help="only list notes whose title or description match <value>. You can repeat this option to search on multiple words.",
                          metavar="<value>")

        parser.add_argument("-k", "--keyword", dest="keyword",
                          help="Group tasks by given keyword instead of project. The '%%' wildcard can be used.",
                          metavar="<keyword>")
        parser.add_argument("--decrypt", dest="decrypt", default=False, action="store_true",
                          help="Decrypt note title and description")
        parser.add_argument("filter", nargs="*", metavar="<project_or_keyword_filter>")

        return parser

    def do_n_list(self, line):
        args, projectList, filters = self._parseListLine(self.parser_n_list(), line)
        if args.decrypt:
            self.cryptoMgr.force_decrypt = True

        filters.append(parseutils.KeywordFilter("@" + NOTE_KEYWORD).filter())
        order = [Task.creationDate, ]
        renderer = TextListRenderer(tui.stdout, cryptoMgr=self.cryptoMgr, renderAsNotes=True)
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
            if not "," in line:
                continue
            ids.append(int(line.split(",")[0]))

        ids.reverse()
        for urgency, taskId in enumerate(ids):
            task = self.session.query(Task).get(taskId)
            task.urgency = urgency
            self.session.merge(task)
        self.session.commit()
    complete_t_reorder = ProjectCompleter(1)

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
        parser.add_argument("--decrypt", dest="decrypt", default=False, action="store_true",
                          help="Decrypt task title and description")
        parser.add_argument("id")
        return parser

    def do_t_show(self, line):
        parser = self.parser_t_show()
        args = parser.parse_args(line)

        if args.decrypt:
            self.cryptoMgr.force_decrypt = True

        task = self.getTaskFromId(args.id)

        title = self.cryptoMgr.decrypt(task.title)
        description = self.cryptoMgr.decrypt(task.description)

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
            fields = [
                ("Project", task.project.name),
                ("Title", title),
                ("ID", task.id),
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

        if args.output in ("all", "description") and task.description:
            if args.output == "all":
                print()
            print(description)

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

        if self.cryptoMgr.isEncrypted(task.title):
            self.cryptoMgr.force_decrypt = True  # Decryption must be turned on to edit
        title = self.cryptoMgr.decrypt(task.title)

        # Create task line
        taskLine = parseutils.createLine("", title, task.getKeywordDict())

        oldCompleter = readline.get_completer()  # Backup previous completer to restore it in the end
        readline.set_completer(editComplete)  # Switch to specific completer

        while True:
            # Edit
            print("(Press Ctrl+C to cancel)")
            try:
                line = tui.editLine(taskLine)
                if not line.strip():
                    tui.warning("Missing title")
                    continue
            except KeyboardInterrupt:
                print()
                print("Cancelled")
                task = None
                break
            foo, title, keywordDict = parseutils.parseLine(task.project.name + " " + line)
            if self.cryptoMgr.isEncrypted(task.title):
                title = self.cryptoMgr.encrypt(title)
            if dbutils.updateTask(task, task.project.name, title, keywordDict):
                break

        readline.set_completer(oldCompleter)  # Restore standard completer
        self.session.merge(task)
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
        task = self.getTaskFromId(tokens[0])
        projectName = tokens[1]
        projectName = self._realProjectName(projectName)

        task.project = dbutils.getOrCreateProject(projectName)
        self.session.merge(task)
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
        self.session.merge(task)
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
        self.session.merge(task)
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
        tokens = parseutils.simplifySpaces(line).split()
        if len(tokens) < 2:
            raise YokadiException("You should give at least two arguments: <task id> <recurrence>")
        task = self.getTaskFromId(tokens[0])

        # Define recurrence:
        freq = byminute = byhour = byweekday = bymonthday = bymonth = None

        tokens[1] = tokens[1].lower()

        if tokens[1] == "none":
            if task.recurrence:
                self.session.delete(task.recurrence)
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
                POSITION = {"first": 1, "second": 2, "third": 3, "fourth": 4, "last":-1}
                if tokens[2].lower() in list(POSITION.keys()) and len(tokens) == 5:
                    byweekday = rrule.weekday(ydateutils.getWeekDayNumberFromDay(tokens[3].lower()),
                                              POSITION[tokens[2]])
                    byhour, byminute = ydateutils.getHourAndMinute(tokens[4])
                    bymonthday = None  # Default to current day number - need to be blanked
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
        self.session.merge(task)
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

# vi: ts=4 sw=4 et
