# -*- coding: UTF-8 -*-
"""
Alias related commands.

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""
from yokadi.core import db
from yokadi.core import dbutils
from yokadi.core.yokadiexception import BadUsageException, YokadiException
from yokadi.ycli import parseutils
from yokadi.ycli import tui
from yokadi.ycli import colors as C


class AliasCmd(object):
    def _aliasExists(self, name):
        return bool(dbutils.getAlias(db.getSession(), name=name, _allowNone=True))

    def do_a_list(self, line):
        """List all aliases."""

        query = db.getSession().query(db.Alias).order_by(db.Alias.name)
        aliases = [(x.name, x.command) for x in query]
        if aliases:
            for name, command in aliases:
                print(C.BOLD + name.ljust(10) + C.RESET + "=> " + command)
        else:
            print("No alias defined. Use a_add to create one")

    def do_a_add(self, line):
        """Add an alias on a command
        Ex. create an alias 'la' for 't_list -a':
        a_add la t_list -a"""
        tokens = line.split()
        if len(tokens) < 2:
            raise BadUsageException("You should provide an alias name and a command")
        name = tokens[0]
        if self._aliasExists(name):
            raise YokadiException("There is already an alias named {}.".format(name))
        command = " ".join(tokens[1:])

        session = db.getSession()
        db.Alias.add(session, name, command)
        session.commit()

    def do_a_edit_name(self, line):
        """Edit the name of an alias.
        a_edit_name <alias name>"""
        session = db.getSession()
        name = line
        if not self._aliasExists(name):
            raise YokadiException("There is no alias named {}".format(name))

        newName = tui.editLine(name)
        newName = parseutils.parseOneWordName(newName)

        if self._aliasExists(newName):
            raise YokadiException("There is already an alias named {}.".format(newName))

        session = db.getSession()
        db.Alias.rename(session, name, newName)
        session.commit()

    def do_a_edit_command(self, line):
        """Edit the command of an alias.
        a_edit_command <alias name>"""
        session = db.getSession()
        name = line
        alias = dbutils.getAlias(db.getSession(), name=name, _allowNone=True)
        if not alias:
            raise YokadiException("There is no alias named {}".format(name))

        command = tui.editLine(alias.command)

        session = db.getSession()
        db.Alias.setCommand(session, name, command)
        session.commit()

    def do_a_remove(self, line):
        """Remove an alias"""
        session = db.getSession()
        alias = dbutils.getAlias(session, name=line, _allowNone=True)
        if not alias:
            tui.error("No alias with that name. Use a_list to display all aliases")
            return
        session.delete(alias)
        session.commit()


def resolveAlias(session, line):
    tokens = line.split(" ", 1)
    if tokens:
        alias = dbutils.getAlias(session, name=tokens[0], _allowNone=True)
        if alias:
            return " ".join([alias.command] + tokens[1:])
    return line


def getAliasesStartingWith(session, text):
    query = session.query(db.Alias).filter(db.Alias.name.startswith(text)).order_by(db.Alias.name)
    return [x.name for x in query]
