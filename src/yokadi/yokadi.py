#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Command line oriented, sqlite powered, todo list

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import locale
import os
import sys
import readline
readline.parse_and_bind("set show-all-if-ambiguous on")
reload(sys)  ## So as to enable setdefaultencoding

import traceback
from cmd import Cmd
from optparse import OptionParser

try:
    from sqlobject import __doc__ as sqlobjectVersion
    from sqlobject import SQLObjectNotFound

except ImportError:
    print "You must install SQLObject to use Yokadi"
    print "Get it on http://www.sqlobject.org/"
    print "Or use 'easy_install sqlobject'"
    sys.exit(1)

import db
from taskcmd import TaskCmd
from projectcmd import ProjectCmd
from keywordcmd import KeywordCmd
from aliascmd import AliasCmd, resolveAlias
from confcmd import ConfCmd
from yokadiexception import YokadiException
import tui
from yokadioptionparser import YokadiOptionParserNormalExitException
import utils

# Force default encoding to prefered encoding
# This is mandatory when yokadi output is piped in another command
sys.setdefaultencoding(tui.ENCODING)


class YokadiCmd(TaskCmd, ProjectCmd, KeywordCmd, ConfCmd, AliasCmd, Cmd):
    def __init__(self):
        Cmd.__init__(self)
        TaskCmd.__init__(self)
        ProjectCmd.__init__(self)
        KeywordCmd.__init__(self)
        AliasCmd.__init__(self)
        ConfCmd.__init__(self)
        self.prompt = "yokadi> "
        self.historyPath=os.path.expandvars("$HOME/.yokadi_history")
        self.loadHistory()

    def emptyline(self):
        """Executed when input is empty. Reimplemented to do nothing."""
        return

    def default(self, line):
        nline = resolveAlias(line, self.aliases)
        if nline != line:
            return self.onecmd(nline)
        elif nline.isdigit():
            self.do_t_show(nline)
        elif nline == "_":
            self.do_t_show(nline)
        else:
            raise YokadiException("Unknown command. Use 'help' to see all available commands")

    def completedefault(self, text, line, begidx, endidx):
        """Default completion command.
        Try to see if command is an alias and find the
        appropriate complete function if it exists"""
        nline = resolveAlias(line, self.aliases)
        compfunc = getattr(self, 'complete_' + nline.split()[0])
        matches = compfunc(text, line, begidx, endidx)
        return matches

    def do_EOF(self, line):
        """Quit."""
        print
        return True

    #Some standard alias
    do_quit=do_EOF
    do_q=do_EOF
    do_exit=do_EOF

    def onecmd(self, line):
        """This method is subclassed just to be
        able to encapsulate it with a try/except bloc"""
        try:
            # Decode user input
            line=line.decode(tui.ENCODING)
            return Cmd.onecmd(self, line)
        except YokadiOptionParserNormalExitException:
            pass
        except YokadiException, e:
            tui.error("*** Yokadi error ***\n\t%s" % e)
        except IOError, e:
            # We can get I/O errors when yokadi is piped onto another shell commands
            # that breaks.
            print >>sys.stderr, "*** I/O error ***\n\t%s" % e
        except KeyboardInterrupt:
            print "*** Break ***"
        except Exception, e:
            tui.error("Unhandled exception (oups)\n\t%s" % e)
            print "This is a bug of Yokadi, sorry."
            print "Send the above message by email to Yokadi developers (ml-yokadi@sequanux.org) to help them make Yokadi better."
            cut="---------------------8<----------------------------------------------"
            print cut
            traceback.print_exc()
            print "--"
            print "Python: %s" % sys.version.replace("\n", " ")
            print "SQLObject: %s" % sqlobjectVersion.replace("\n", " ")
            print "OS: %s (%s)" % os.uname()[0:3:2]
            print "Yokadi: %s" % utils.currentVersion()
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

    def do_help(self, arg):
        """Type help <topic> to see the help for a given topic"""

        """
        Overload do_help to show help from the command parser if it exists:
        if there is a parser_foo() method, assume this method returns a
        YokadiOptionParser for the do_foo() method and show the help of the
        parser, instead of do_foo() docstring.
        """
        if arg in self.aliases:
            # If arg is an alias, get help on the underlying command
            arg = self.aliases[arg].split()[0]
        if hasattr(self, "parser_" + arg):
            parserMethod = getattr(self, "parser_" + arg)
            parserMethod().print_help(sys.stderr)
        else:
            print "Usage: ",
            Cmd.do_help(self, arg)

    def completenames(self, text, *ignored):
        """Complete commands names. Same as Cmd.cmd one but with support
        for command aliases. Code kindly borrowed to Pysql"""
        dotext = 'do_'+text
        names = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        names.extend([a for a in self.aliases.keys() if a.startswith(text)])
        return names


def main():
    locale.setlocale(locale.LC_ALL, os.environ.get("LANG", "C"))
    parser = OptionParser()

    parser.add_option("-d", "--db", dest="filename",
                      help="TODO database", metavar="FILE")

    parser.add_option("-c", "--create-only",
                      dest="createOnly", default=False, action="store_true",
                      help="Just create an empty database")

    parser.add_option("-v", "--version",
                      dest="version", action="store_true",
                      help="Display Yokadi current version")

    (options, args) = parser.parse_args()

    if options.version:
        print "Yokadi - %s" % utils.currentVersion()
        return

    if not options.filename:
        # Look if user define an env VAR for yokadi db
        options.filename=os.getenv("YOKADI_DB")
        if options.filename:
            print "Using env defined database (%s)" % options.filename
        else:
            options.filename=os.path.normcase(os.path.expanduser("~/.yokadi.db"))
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
