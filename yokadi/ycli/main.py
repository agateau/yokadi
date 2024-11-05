#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Command line oriented, sqlite powered, todo list

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import locale
import os
import platform
import sys

import readline

import traceback
from cmd import Cmd
from argparse import ArgumentParser

import sqlalchemy
from colorama import just_fix_windows_console

import yokadi

from yokadi.core import db
from yokadi.core import basepaths
from yokadi.core import fileutils
from yokadi.update import update

from yokadi.ycli import tui, commonargs
from yokadi.ycli.aliascmd import AliasCmd, resolveAlias
from yokadi.ycli.confcmd import ConfCmd
from yokadi.ycli.keywordcmd import KeywordCmd
from yokadi.ycli.projectcmd import ProjectCmd
from yokadi.ycli.taskcmd import TaskCmd
from yokadi.core.yokadiexception import YokadiException, BadUsageException
from yokadi.core.yokadioptionparser import YokadiOptionParserNormalExitException

readline.parse_and_bind("set show-all-if-ambiguous on")


# TODO: move YokadiCmd to a separate module in ycli package
class YokadiCmd(TaskCmd, ProjectCmd, KeywordCmd, ConfCmd, AliasCmd, Cmd):
    def __init__(self):
        Cmd.__init__(self)
        TaskCmd.__init__(self)
        ProjectCmd.__init__(self)
        KeywordCmd.__init__(self)
        AliasCmd.__init__(self)
        ConfCmd.__init__(self)
        self.prompt = "yokadi> "
        self.historyPath = basepaths.getHistoryPath()
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
        print()
        return True

    # Some standard alias
    do_quit = do_EOF
    do_q = do_EOF
    do_exit = do_EOF

    def onecmd(self, line):
        """This method is subclassed just to be
        able to encapsulate it with a try/except bloc"""
        try:
            # Decode user input
            line = line
            return Cmd.onecmd(self, line)
        except YokadiOptionParserNormalExitException:
            pass
        except UnicodeDecodeError as e:
            tui.error("Unicode decoding error. Please check you locale and terminal settings (%s)." % e)
        except UnicodeEncodeError as e:
            tui.error("Unicode encoding error. Please check you locale and terminal settings (%s)." % e)
        except BadUsageException as e:
            tui.error("*** Bad usage ***\n\t%s" % e)
            cmd = line.split(' ')[0]
            self.do_help(cmd)
        except YokadiException as e:
            tui.error("*** Yokadi error ***\n\t%s" % e)
        except IOError as e:
            # We can get I/O errors when yokadi is piped onto another shell commands
            # that breaks.
            print("*** I/O error ***\n\t%s" % e, file=sys.stderr)
        except KeyboardInterrupt:
            print("*** Break ***")
        except Exception as e:
            tui.error("Unhandled exception (oups)\n\t%s" % e)
            print("This is a bug of Yokadi, sorry.")
            print("Send the above message by email to Yokadi developers (ml-yokadi@sequanux.org) to help them make"
                  " Yokadi better.")
            cut = "---------------------8<----------------------------------------------"
            print(cut)
            traceback.print_exc()
            print("--")
            print("Python: %s" % sys.version.replace("\n", " "))
            print("SQL Alchemy: %s" % sqlalchemy.__version__)
            print("OS: %s" % platform.system())
            print("Yokadi: %s" % yokadi.__version__)
            print(cut)
            print()

    def loadHistory(self):
        """Tries to load previous history list from disk"""
        try:
            readline.read_history_file(self.historyPath)
        except Exception:
            # Cannot load any previous history. Start from a clear one
            pass

    def writeHistory(self):
        """Writes shell history to disk"""
        try:
            fileutils.createParentDirs(self.historyPath)
            # Open r/w and close file to create one if needed
            historyFile = open(self.historyPath, "w", encoding='utf-8')
            historyFile.close()
            readline.set_history_length(1000)
            readline.write_history_file(self.historyPath)
        except Exception as e:
            tui.warning("Fail to save history to %s. Error was:\n\t%s"
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
            print("Usage: ", end=' ')
            Cmd.do_help(self, arg)

    def completenames(self, text, *ignored):
        """Complete commands names. Same as Cmd.cmd one but with support
        for command aliases. Code kindly borrowed to Pysql"""
        dotext = 'do_' + text
        names = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        names.extend([a for a in list(self.aliases.keys()) if a.startswith(text)])
        return names


def createArgumentParser():
    parser = ArgumentParser()
    commonargs.addArgs(parser)

    parser.add_argument("-c", "--create-only",
                        dest="createOnly", default=False, action="store_true",
                        help="Just create an empty database")

    parser.add_argument("-u", "--update",
                        dest="update", action="store_true",
                        help="Update database to the latest version")

    parser.add_argument('cmd', nargs='*')
    return parser


def main():
    locale.setlocale(locale.LC_ALL, os.environ.get("LANG", "C"))
    just_fix_windows_console()

    parser = createArgumentParser()
    args = parser.parse_args()
    dataDir, dbPath = commonargs.processArgs(args)

    basepaths.migrateOldHistory()
    try:
        basepaths.migrateOldDb(dbPath)
    except basepaths.MigrationException as exc:
        print(exc)
        return 1

    if args.update:
        return update.update(dbPath)

    try:
        db.connectDatabase(dbPath)
    except db.DbUserException as exc:
        print(exc)
        return 1

    if args.createOnly:
        return 0
    db.setDefaultConfig()  # Set default config parameters

    cmd = YokadiCmd()

    try:
        if len(args.cmd) > 0:
            print(" ".join(args.cmd))
            cmd.onecmd(" ".join(args.cmd))
        else:
            cmd.cmdloop()
    except KeyboardInterrupt:
        print("\n\tBreak ! (the nice way to quit is 'quit' or 'EOF' (ctrl-d)")
        return 1
    # Save history
    cmd.writeHistory()
    return 0


if __name__ == "__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
