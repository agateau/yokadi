from cmd import Cmd
from datetime import datetime

from db import *
import utils
import parseutils
import tui
from textrenderer import TextRenderer
from bugcmd import BugCmd

class YCmd(Cmd,BugCmd):
    __slots__ = ["renderer"]
    def __init__(self):
        Cmd.__init__(self)
        BugCmd.__init__(self)
        self.prompt = "yokadi> "
        self.renderer = TextRenderer()

    def do_t_add(self, line):
        """Add new task. Will prompt to create properties if they do not exist.
        t_add <projectName> [-p <property1>] [-p <property2>] <Task description>"""
        projectName, title, propertyDict = parseutils.parseTaskLine(line)
        task = utils.addTask(projectName, title, propertyDict)
        if task:
            print "Added task '%s' (id=%d)" % (title, task.id)

    def do_t_describe(self, line):
        """Starts an editor to enter a longer description of a task.
        t_describe <id>"""
        taskId = int(line)
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
        taskId = int(line)
        task = Task.get(taskId)
        task.status = 'started'

    def do_t_mark_done(self, line):
        """Mark task as done.
        t_mark_done <id>"""
        taskId = int(line)
        task = Task.get(taskId)
        task.status = 'done'

    def do_t_mark_new(self, line):
        """Mark task as new (not started).
        t_mark_new <id>"""
        taskId = int(line)
        task = Task.get(taskId)
        task.status = 'new'

    def do_t_apply(self, line):
        """Apply a command to several tasks.
        t_apply <id1>[,<id2>,[<id3>]...]] <command> <args>"""
        tokens = line.split(" ", 2)
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
        taskId = int(line)
        Task.delete(taskId)

    def do_t_list(self, line):
        """List tasks by project and/or properties.
        <project_name> can be '*' to list all projects.
        t_list <project_name> [<property1> [<property2>]...]
        """
        tokens = line.strip().split(' ')
        projectName = tokens[0]
        if projectName != '*':
            projectList = Project.selectBy(name=projectName)
        else:
            projectList = Project.select()

        if len(tokens) > 1:
            propertySet = set([Property.byName(x) for x in tokens[1:]])
        else:
            propertySet = None

        for project in projectList:
            taskList = Task.select(AND(Task.q.projectID == project.id,
                                       Task.q.status    != 'done'),
                                   orderBy=-Task.q.urgency)

            if propertySet:
                # FIXME: Optimize
                taskList = [x for x in taskList if propertySet.issubset(set(x.properties))]
            else:
                taskList = list(taskList)

            if len(taskList) == 0:
                continue

            self.renderer.renderTaskListHeader(project.name)
            for task in taskList:
                self.renderer.renderTaskListRow(task)

    def do_t_reorder(self, line):
        """Reorder tasks of a project.
        It works by starting an editor with the task list: you can then change
        the order of the lines and save the list. The urgency field will be
        updated to match the order.
        t_reorder <project_name>"""
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


    def do_t_prop_set(self, line):
        """Set a task property.
        t_prop_set <id> <property> [<value>]"""

        # Parse line
        line = parseutils.simplifySpaces(line)
        tokens = line.split(" ")
        taskId = int(tokens[0])
        propertyName = tokens[1]
        if len(tokens) > 2:
            value = int(tokens[2])
        else:
            value = None

        # Get task and property
        task = Task.get(taskId)
        property = utils.getOrCreateProperty(propertyName)
        if not property:
            return

        # Assign property
        property = TaskProperty(task=task, property=property, value=value)

    def do_t_show(self, line):
        """Display details of a task.
        t_show <id>"""
        taskId = int(line)
        task = Task.get(taskId)
        self.renderer.renderTaskDetails(task)


    def do_t_edit(self, line):
        """Edit a task.
        t_edit <id>"""
        taskId = int(line)
        task = Task.get(taskId)

        # Create task line
        taskLine = parseutils.createTaskLine(task.project.name, task.title, task.getPropertyDict())

        # Edit
        line = tui.editLine(taskLine)

        # Update task
        projectName, title, propertyDict = parseutils.parseTaskLine(line)
        if not utils.createMissingProperties(propertyDict.keys()):
            return
        task.project = utils.getOrCreateProject(projectName)
        task.title = title
        task.setPropertyDict(propertyDict)


    def do_p_list(self, line):
        """List all properties."""
        for property in Property.select():
            print property.name


    def do_import_yagtd(self, line):
        """Import a line from yagtd"""
        print "Importing '%s'..." % line
        line = line.replace("@", "-p c/")
        line = line.replace("p:", "-p p/")
        line, complete = parseutils.extractYagtdField(line, "C:")
        line, creationDate = parseutils.extractYagtdField(line, "S:")
        line, urgency = parseutils.extractYagtdField(line, "U:")
        line, bug = parseutils.extractYagtdField(line, "bug:")
        line, duration = parseutils.extractYagtdField(line, "T:")
        line, importance = parseutils.extractYagtdField(line, "I:")

        if complete == "100":
            status = "done"
        elif complete == "0" or complete is None:
            status = "new"
        else:
            status = "started"

        if creationDate:
            creationDate = datetime.strptime(creationDate, '%Y-%m-%d')
        else:
            creationDate = datetime.now()

        urgency = int(urgency)

        title, propertyNames = parseutils.parseTaskLine(line)

        # Create task
        task = Task(
            creationDate = creationDate,
            title=title,
            description="",
            urgency=urgency,
            status=status)

        # Create properties
        propertySet = set()
        for propertyName in propertyNames:
            property = utils.getOrCreateProperty(propertyName, interactive=False)
            propertySet.add(property)
        for property in propertySet:
            task.addProperty(property)

        if bug:
            bug = int(bug)
            property = utils.getOrCreateProperty("bug", interactive=False)
            TaskProperty(task=task, property=property, value=bug)


    def do_EOF(self, line):
        """Quit."""
        print
        return True
# vi: ts=4 sw=4 et
