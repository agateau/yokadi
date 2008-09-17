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

from sqlobject import connectionForURI, sqlhub, SQLObjectNotFound

import db
from taskcmd import TaskCmd
from projectcmd import ProjectCmd
from keywordcmd import KeywordCmd
from confcmd import ConfCmd
from bugcmd import BugCmd
from utils import YokadiException
import colors as C

# Yokadi database version needed for this code
# If database config keyDB_VERSION differ from this one
# a database migration is required
DB_VERSION="2"

# Default user encoding. Used to decode all input strings
ENCODING=locale.getpreferredencoding()


class YokadiCmd(Cmd, TaskCmd, ProjectCmd, KeywordCmd, BugCmd, ConfCmd):
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

def setDefaultConfig():
    """Set default config parameter in database if they (still) do not exist"""
    #TODO: also set DB_VERSION here ?
    defaultConfig={
        "TEXT_WIDTH"    : ("60", False)}

    for name, value in defaultConfig.items():
        if db.Config.select(db.Config.q.name==name).count()==0:
            db.Config(name=name, value=value[0], system=value[1])

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
        # Set database version according to current yokadi release
        db.Config(name="DB_VERSION", value=DB_VERSION, system=True)
    else:
        # Ensure Config table exist
        if not db.Config.tableExists():
            # So we have juste migrated from a yokadi without Config
            print "Configuration table does not exist. Creating it"
            db.Config.createTable()
            db.Config(name="DB_VERSION", value="1", system=True)
        # Check that the current database version is aligned with Yokadi code
        try:
            version=db.Config.byName("DB_VERSION").value
        except SQLObjectNotFound:
            # Ok, we have a Config table but no DB_VERSION key. Quite strange. Default to version 1
            print "Oups. Config table does not have the DB_VERSION key. Creating it with default value 1"
            db.Config(name="DB_VERSION", value="1")
            version="1"
        if version!=DB_VERSION:
            print C.BOLD+C.RED+"Your database version is %s wether your Yokadi code wants version %s." \
                % (version, DB_VERSION) + C.RESET
            print "Please, run the update.py script to migrate your database prior to running Yokadi"
            sys.exit(1)

    if options.createOnly:
        return

    setDefaultConfig() # Set default config parameters

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
