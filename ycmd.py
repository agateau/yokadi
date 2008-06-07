from cmd import Cmd
from datetime import datetime

from db import *

class YCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        Cmd.prompt = "yokadi> "
        self.interactive = True

    def do_t_add(self, line):
        """Add new task to a project. Will prompt to create project if it does not exists.
        t_add Project Task description"""
        projectName, rest = line.split(" ", 1)
        results = Project.select(Project.q.name ==  projectName)
        lst = list(results)
        if len(lst) > 0:
            prj = lst[0]
        else:
            while self.interactive:
                answer = raw_input("Project '%s' does not exist, create it (y/n)? " % projectName)
                if answer == "n":
                    return
                if answer == "y":
                    break
            prj = Project(name=projectName)
            print "Added project '%s'" % projectName

        task = Task(creationDate = datetime.now(), title=rest, description="", status="new", project=prj)
        print "Added task '%s' (%d)" % (rest, task.id)

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
        line = line.strip()
        if line != "":
            crit = [Project.q.name == line]
        else:
            crit = []

        prjList = Project.select(*crit)

        for prj in prjList:
            print
            print "Project: %s" % prj.name
            for task in prj.tasks:
                if task.status != 'done':
                    print task.toUtf8()

    def do_p_list(self, line):
        results = Project.select()
        for prj in results:
            print prj.name

    def do_EOF(self, line):
        print
        return True
# vi: ts=4 sw=4 et
