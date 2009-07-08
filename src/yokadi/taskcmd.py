# -*- coding: UTF-8 -*-
"""
Task related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""
import os
from datetime import datetime, date, timedelta
from dateutil import rrule
from sqlobject import SQLObjectNotFound, LIKE, AND, OR

from db import Config, Keyword, Project, Task, Recurrence
import dbutils
import dateutils
import parseutils
import tui
from completers import ProjectCompleter, projectAndKeywordCompleter,\
                       taskIdCompleter, recurrenceCompleter
from yokadiexception import YokadiException
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

class TaskCmd(object):
    def do_t_add(self, line):
        """Add new task. Will prompt to create keywords if they do not exist.
        t_add <projectName> [@<keyword1>] [@<keyword2>] <Task description>"""
        if not line:
            print "Give at least a task name !"
            return
        projectName, title, keywordDict = parseutils.parseLine(line)
        if not title:
            raise YokadiException("You should give a task title")
        task = dbutils.addTask(projectName, title, keywordDict)
        if task:
            print "Added task '%s' (id=%d)" % (title, task.id)
        else:
            tui.reinjectInRawInput(u"t_add " + line)

    complete_t_add = projectAndKeywordCompleter

    def do_t_describe(self, line):
        """Starts an editor to enter a longer description of a task.
        t_describe <id>"""
        task=dbutils.getTaskFromId(line)
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
        tokens = line.split(" ")
        if len(tokens)!=2:
            raise YokadiException("You must provide a taskId and an urgency value") 
        task = dbutils.getTaskFromId(tokens[0])
        try:
            # Do not use isdigit(), so that we can set negative urgency. This
            # make it possible to stick tasks to the bottom of the list.
            urgency = int(tokens[1])
        except ValueError:
            raise YokadiException("Task urgency must be a digit")

        if urgency>100:
            tui.warning("Max urgency is 100")
            urgency=100
        elif urgency<-99:
            tui.warning("Min urgency is -99")
            urgency=-99

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
        task=dbutils.getTaskFromId(line)
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
        task=dbutils.getTaskFromId(' '.join(args))
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
        filters=[]
        filters.append(Task.q.status=="done")
        filters.append(Task.q.doneDate<(datetime.now()-timedelta(days=options.delay)))
        tasks=Task.select(AND(*filters))
        if tasks.count()==0:
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

        parser.add_option("-s", "--search", dest="search",
                          action="append",
                          help="only list tasks which title or description match <value>",
                          metavar="<search>[=<value>]")

        formatList = ["auto"] + gRendererClassDict.keys()
        parser.add_option("-f", "--format", dest="format",
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
            projectName, keywordDict = parseutils.extractKeywords(u" ".join(args))
            projectName = projectName.rstrip(":")
        else:
            projectName = ""
            keywordDict = {}

        if not projectName:
            # Take all project if none provided
            projectName="%"

        projectList = Project.select(LIKE(Project.q.name, projectName))

        if projectList.count()==0:
            tui.error("Found no project matching '%s'" % projectName)
            return

        # Check keywords exist
        for keyword in keywordDict.keys():
            try:
                Keyword.byName(keyword)
            except SQLObjectNotFound:
                tui.error("Keyword %s is unknown." % keyword)
                return

        # Filtering and sorting according to parameters
        filters=[]
        order=-Task.q.urgency, Task.q.creationDate
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
        if options.search:
            for word in options.search:
                filters.append(OR(LIKE(Task.q.title, "%"+word+"%"),
                                  LIKE(Task.q.description, "%"+word+"%")))

        # Define output
        if options.output:
            out = open(options.output, "w")
        else:
            out = tui.stdout

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
                taskList = [x for x in taskList if (keywordDictIsSubsetOf(x.getKeywordDict(), keywordDict) or
                                                    keywordDictIsSubsetOf(x.project.getKeywordDict(), keywordDict))]
            else:
                taskList = list(taskList)

            if len(taskList) == 0:
                continue

            renderer.addTaskList(project, taskList)
        renderer.end()

        if len(hiddenProjectNames) > 0:
            tui.info("hidden projects: %s" % ", ".join(hiddenProjectNames))

    complete_t_list = projectAndKeywordCompleter

    def do_t_reorder(self, line):
        """Reorder tasks of a project.
        It works by starting an editor with the task list: you can then change
        the order of the lines and save the list. The urgency field will be
        updated to match the order.
        t_reorder <project_name>"""
        projectName = line.rstrip(":")
        project = Project.byName(projectName)
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

        task=dbutils.getTaskFromId(' '.join(args))

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

    def do_t_edit(self, line):
        """Edit a task.
        t_edit <id>"""
        task = dbutils.getTaskFromId(line)

        # Create task line
        taskLine = parseutils.createLine("", task.title, task.getKeywordDict())

        while True:
            # Edit
            print "(Press Ctrl+C to cancel)"
            try:
                line = tui.editLine(taskLine)
                if not line.strip():
                    tui.warning("Indicate a task title !")
                    continue
            except KeyboardInterrupt:
                print
                print "Cancelled"
                return
            foo, title, keywordDict = parseutils.parseLine(task.project.name+" "+line)
            if dbutils.updateTask(task, task.project.name, title, keywordDict):
                break

    complete_t_edit = taskIdCompleter

    def do_t_set_project(self, line):
        """@deprecated: should be removed"""
        tui.warnDeprecated("t_set_project", "t_project")
        self.do_t_project(line)


    def do_t_project(self, line):
        """Set task's project.
        t_project <id> <project>"""
        tokens = line.split(" ")
        if len(tokens)!=2:
            raise YokadiException("You should give two arguments: <task id> <project>")
        task=dbutils.getTaskFromId(tokens[0])
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

        Or as an absolute date or time:
        - 10:38:            at 10:38 today
        - 25/09/2010 12:10: on the 25th of September, 2010, at 12:10
        - 23/02/2010:       on the 23th of February, 2010
        - 01/04:            on the 1st of April
        - 12:               on the 12th of current month

        To reset a due date, use "none"."""
        if len(line.split())<2:
            raise YokadiException("Give a task id and time, date or date & time")
        taskId, line=line.strip().split(" ", 1)
        task=dbutils.getTaskFromId(taskId)

        if line.lower()=="none":
            task.dueDate=None
            print "Due date for task '%s' reset" % task.title
        else:
            task.dueDate = dateutils.parseHumaneDateTime(line)
            print "Due date for task '%s' set to %s" % (task.title, task.dueDate.ctime())

    complete_t_set_due = taskIdCompleter
    complete_t_due = taskIdCompleter

    def do_t_add_keywords(self, line):
        """Add keywords to an existing task
        t_add_keyword <id> <keyword1> <keyword2>[=<value>]...
        """
        tokens = line.split(" ", 1)
        if len(tokens) < 2:
            raise YokadiException("You should give at least two arguments: <task id> <keyword>")
        task = dbutils.getTaskFromId(tokens[0])
        remainingText, newKwDict = parseutils.extractKeywords(tokens[1])

        dbutils.createMissingKeywords(newKwDict.keys())

        kwDict = task.getKeywordDict()
        kwDict.update(newKwDict)
        task.setKeywordDict(kwDict)

    def do_t_recurs(self, line):
        """Make a task recurs
        t_recurs <id> yearly <dd/mm> <HH:MM>
        t_recurs <id> monthly <dd> <HH:MM>
        t_recurs <id> monthly <first/second/third/last> <mo, tu, we, th, fr, sa, su> <hh:mm>
        t_recurs <id> weekly <mo, tu, we, th, fr, sa, su> <hh:mm>
        t_recurs <id> daily <HH:MM>
        t_recurs <id> none (remove recurrence)"""
        tokens = line.split()
        if len(tokens) < 2:
            raise YokadiException("You should give at least two arguments: <task id> <recurrence>")
        task = dbutils.getTaskFromId(tokens[0])
        
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
            byhour, byminute = dateutils.getHourAndMinute(tokens[2])
        elif tokens[1] == "weekly":
            freq = rrule.WEEKLY
            if len(tokens) != 4:
                raise YokadiException("You should give day and time for weekly task")
            byweekday = dateutils.getWeekDayNumberFromDay(tokens[2].lower())
            byhour, byminute = dateutils.getHourAndMinute(tokens[3])
        elif tokens[1] == "monthly":
            freq = rrule.MONTHLY
            if len(tokens) < 4:
                raise YokadiException("You should give day and time for monthly task")
            try:
                bymonthday = int(tokens[2])
                byhour, byminute = dateutils.getHourAndMinute(tokens[3])
            except ValueError:
                POSITION = { "first" : 1, "second" : 2, "third" : 3, "fourth" : 4, "last" : -1 }
                if tokens[2].lower() in POSITION.keys() and len(tokens) == 5:
                    byweekday = rrule.weekday(dateutils.getWeekDayNumberFromDay(tokens[3].lower()),
                                              POSITION[tokens[2]])
                    byhour, byminute = dateutils.getHourAndMinute(tokens[4])
                    bymonthday = None # Default to current day number - need to be blanked                    
                else:
                    raise YokadiException("Unable to understand date. See help t_recurs for details")
        elif tokens[1] == "yearly":
            freq = rrule.YEARLY
            rDate = dateutils.parseHumaneDateTime(" ".join(tokens[2:]))
            bymonth = rDate.month
            bymonthday = rDate.day
        else:
            raise YokadiException("Unknown frequency. Available: daily, weekly, monthly and yearly")

        if task.recurrence is None:
            task.recurrence = Recurrence()
        rr = rrule.rrule(freq, byhour=byhour, byminute=byminute, byweekday=byweekday,
                         bymonthday=bymonthday, bymonth=bymonth)
        task.recurrence.setRrule(rr)
        task.dueDate = task.recurrence.getNext()
    complete_t_recurs = recurrenceCompleter
# vi: ts=4 sw=4 et