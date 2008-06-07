from cmd import Cmd
from datetime import datetime

from db import *
import utils
from textrenderer import TextRenderer

class YCmd(Cmd):
    __slots__ = ["renderer"]
    def __init__(self):
        Cmd.__init__(self)
        self.prompt = "yokadi> "
        self.renderer = TextRenderer()

    def do_t_add(self, line):
        """Add new task. Will prompt to create properties if they do not exist.
        t_add [-p property1] [-p property2] Task description"""
        title, propertyNames = utils.extractProperties(line)
        propertySet = set()
        for propertyName in propertyNames:
            property = utils.getOrCreateProperty(propertyName)
            if not property:
                return
            propertySet.add(property)
        task = Task(creationDate = datetime.now(), title=title, description="", status="new")
        for property in propertySet:
            task.addProperty(property)
        print "Added task '%s' (%d)" % (title, task.id)

    def do_t_mark_started(self, line):
        taskId = int(line)
        task = Task.get(taskId)
        task.status = 'started'

    def do_t_mark_done(self, line):
        taskId = int(line)
        task = Task.get(taskId)
        task.status = 'done'

    def do_t_mark_new(self, line):
        taskId = int(line)
        task = Task.get(taskId)
        task.status = 'new'

    def do_t_apply(self, line):
        """Apply command to several tasks:
        t_apply id1,id2,id3 command [args]"""
        tokens = line.split(" ", 2)
        idStringList = tokens[0]
        cmd = tokens[1]
        if len(tokens) == 3:
            args = tokens[3]
        else:
            args = ""
        ids = [int(x) for x in idStringList.split(",")]
        for id in ids:
            line = " ".join([cmd, str(id), args])
            self.onecmd(line.strip())

    def do_t_remove(self, line):
        taskId = int(line)
        Task.delete(taskId)

    def do_t_list(self, line):
        """List tasks assigned specific properties, or all tasks if no property is
        specified.
        t_list [property1] [property2]
        """
        line = line.strip()
        if line != "":
            propertySet = set([Property.byName(x) for x in line.split(" ")])
        else:
            propertySet = None

        # FIXME: Optimize
        self.renderer.renderTaskListHeader()
        for task in Task.select():
            if propertySet:
                taskPropertySet = set(task.properties)
                if not propertySet.issubset(taskPropertySet):
                    continue

            if task.status != 'done':
                self.renderer.renderTaskListRow(task)

    def do_t_prop_set(self, line):
        """Set a task property
        t_prop_set id property [value]"""

        # Parse line
        line = utils.simplifySpaces(line)
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
        """Display details of a task
        t_show id"""
        taskId = int(line)
        task = Task.get(taskId)
        self.renderer.renderTaskDetails(task)


    def do_p_list(self, line):
        """List all properties"""
        for property in Property.select():
            print property.name


    def do_import_yagtd(self, line):
        """Import a line from yagtd"""
        print "Importing '%s'..." % line
        line = line.replace("@", "-p c/")
        line = line.replace("p:", "-p p/")
        line, complete = utils.extractYagtdField(line, "C:")
        line, creationDate = utils.extractYagtdField(line, "S:")
        line, urgency = utils.extractYagtdField(line, "U:")
        line, bug = utils.extractYagtdField(line, "bug:")
        line, duration = utils.extractYagtdField(line, "T:")
        line, importance = utils.extractYagtdField(line, "I:")

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

        title, propertyNames = utils.extractProperties(line)

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
        """Quit"""
        print
        return True
# vi: ts=4 sw=4 et
