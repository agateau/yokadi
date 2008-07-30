#!/usr/bin/env python
import os
from cmd import Cmd
from optparse import OptionParser

from sqlobject import *

import db
from taskcmd import TaskCmd
from projectcmd import ProjectCmd
from keywordcmd import KeywordCmd
from bugcmd import BugCmd

class YokadiCmd(Cmd, TaskCmd, ProjectCmd, KeywordCmd, BugCmd):
    def __init__(self):
        Cmd.__init__(self)
        TaskCmd.__init__(self)
        ProjectCmd.__init__(self)
        KeywordCmd.__init__(self)
        BugCmd.__init__(self)
        self.prompt = "yokadi> "

    def do_EOF(self, line):
        """Quit."""
        print
        return True


def main():
    parser = OptionParser()

    parser.add_option("--db", dest="filename",
                      help="TODO database", metavar="FILE")

    parser.add_option("--create-only",
                      dest="createOnly", default=False, action="store_true",
                      help="Just create an empty database")

    (options, args) = parser.parse_args()

    dbFileName = os.path.abspath(options.filename)
    connectionString = 'sqlite:' + dbFileName
    connection = connectionForURI(connectionString)
    sqlhub.processConnection = connection
    if not os.path.exists(dbFileName):
        print "Creating database"
        db.createTables()

    if options.createOnly:
        return

    cmd = YokadiCmd()
    if len(args) > 0:
        cmd.onecmd(" ".join(args))
    else:
        cmd.cmdloop()


if __name__=="__main__":
    main()
# vi: ts=4 sw=4 et
