#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Command line oriented, sqlite powered, todo list

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import os
import sys
import readline
import traceback
import locale
from cmd import Cmd
from optparse import OptionParser

import db
from taskcmd import TaskCmd
from projectcmd import ProjectCmd
from keywordcmd import KeywordCmd
from confcmd import ConfCmd
from bugcmd import BugCmd
from utils import YokadiException
from utils import ENCODING
from yokadioptionparser import YokadiOptionParserNormalExitException
import colors as C

# Force default encoding to prefered encoding
# This is mandatory when yokadi output is piped in another command
reload(sys)
sys.setdefaultencoding(ENCODING)


class YokadiCmd(TaskCmd, ProjectCmd, KeywordCmd, BugCmd, ConfCmd, Cmd):
    def __init__(self):
        Cmd.__init__(self)
        TaskCmd.__init__(self)
        ProjectCmd.__init__(self)
        KeywordCmd.__init__(self)
        BugCmd.__init__(self)
        self.prompt = "yokadi> "
        self.historyPath=os.path.expandvars("$HOME/.yokadi_history")
        self.loadHistory()

    def emptyline(self):
        """Executed when input is empty. Reimplemented to do nothing."""
        return

    def default(self, line):
        if line.isdigit():
            self.do_t_show(line)
        else:
            raise YokadiException("Unknown command. Use 'help' to see all available commands")

    def do_EOF(self, line):
        """Quit."""
        print
        return True
    #Some alias
    do_quit=do_EOF
    do_q=do_EOF
    do_exit=do_EOF

    def onecmd(self, line):
        """This method is subclassed just to be
        able to encapsulate it with a try/except bloc"""
        try:
            # Decode user input
            line=line.decode(ENCODING)
            return Cmd.onecmd(self, line)
        except YokadiOptionParserNormalExitException:
            pass
        except YokadiException, e:
            print C.RED+C.BOLD+"*** Yokadi error ***\n\t%s" % e + C.RESET
        except KeyboardInterrupt:
            print C.RED+C.BOLD+"*** Break ***"+C.RESET
        except Exception, e:
            print C.RED+C.BOLD+"*** Unhandled error (oups)***\n\t%s" % e + C.RESET
            print C.BOLD+"This is a bug of Yokadi, sorry."
            print "Send the above message by email to Yokadi developers to help them make Yokadi better."+C.RESET
            cut="---------------------8<----------------------------------------------"
            print cut
            traceback.print_exc()
            print cut
            print

    def loadHistory(self):
        """Tries to load previous history list from disk"""
        try:
            readline.read_history_file(self.historyPath)
        except Exception, e:
            # Cannot load any previous history. Start from a clear one
            pass

    def writeHistory(self):
        """Writes shell history to disk"""
        try:
            # Open r/w and close file to create one if needed
            historyFile=file(self.historyPath, "w")
            historyFile.close()
            readline.set_history_length(1000)
            readline.write_history_file(self.historyPath)
        except Exception, e:
            raise YokadiException("Fail to save history to %s. Error was:\n\t%s"
                        % (self.historyPath, e))

def main():
    parser = OptionParser()

    parser.add_option("-d", "--db", dest="filename",
                      help="TODO database", metavar="FILE")

    parser.add_option("-c", "--create-only",
                      dest="createOnly", default=False, action="store_true",
                      help="Just create an empty database")

    (options, args) = parser.parse_args()

    if not options.filename:
        options.filename=os.path.join(os.path.expandvars("$HOME"), ".yokadi.db")
        print "Using default database (%s)" % options.filename

    db.connectDatabase(options.filename)

    if options.createOnly:
        return

    db.setDefaultConfig() # Set default config parameters

    cmd = YokadiCmd()
    try:
        if len(args) > 0:
            cmd.onecmd(" ".join(args))
        else:
            cmd.cmdloop()
    except KeyboardInterrupt:
        print "\n\tBreak ! (the nice way to quit is 'quit' or 'EOF' (ctrl-d)"
        sys.exit(1)
    # Save history
    cmd.writeHistory()

if __name__=="__main__":
    main()
# vi: ts=4 sw=4 et
