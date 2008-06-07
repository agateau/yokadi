from cmd import Cmd
from datetime import datetime

from db import *
import utils

class YCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.prompt = "yokadi> "

    def do_t_add(self, line):
        """Add new task. Will prompt to create keywords if they do not exist.
        t_add [-k keyword1] [-k keyword2] Task description"""
        title, keywordNames = utils.extractKeywords(line)
        keywordSet = set()
        for keywordName in keywordNames:
            keyword = utils.getOrCreateKeyword(keywordName)
            if not keyword:
                return
            keywordSet.add(keyword)
        task = Task(creationDate = datetime.now(), title=title, description="", status="new")
        for keyword in keywordSet:
            task.addKeyword(keyword)
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
        """List tasks assigned specific keywords, or all tasks if no keyword is
        specified.
        t_list [keyword1] [keyword2]
        """
        line = line.strip()
        if line != "":
            keywordSet = set([Keyword.byName(x) for x in line.split(" ")])
        else:
            keywordSet = None

        # FIXME: Optimize
        for task in Task.select():
            if keywordSet:
                taskKeywordSet = set(task.keywords)
                if not keywordSet.issubset(taskKeywordSet):
                    continue

            if task.status != 'done':
                print task.toUtf8()

    def do_k_list(self, line):
        """List all keywords"""
        for keyword in Keyword.select():
            print keyword.name


    def do_import_yagtd(self, line):
        """Import a line from yagtd"""
        print "Importing '%s'..." % line
        line = line.replace("@", "-k c/")
        line = line.replace("p:", "-k p/")
        line, complete = utils.extractYagtdField(line, "C:")
        line, creationDate = utils.extractYagtdField(line, "S:")

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

        title, keywordNames = utils.extractKeywords(line)
        keywordSet = set()
        for keywordName in keywordNames:
            keyword = utils.getOrCreateKeyword(keywordName, interactive=False)
            keywordSet.add(keyword)
        task = Task(creationDate = creationDate, title=title, description="", status=status)
        for keyword in keywordSet:
            task.addKeyword(keyword)


    def do_EOF(self, line):
        """Quit"""
        print
        return True
# vi: ts=4 sw=4 et
