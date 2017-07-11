# -*- coding: UTF-8 -*-
"""
Alias related commands.

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""
from yokadi.core import db
from yokadi.core.yokadiexception import BadUsageException, YokadiException
from yokadi.ycli.basicparseutils import parseOneWordName
from yokadi.ycli import tui
from yokadi.ycli import colors


class AliasCmd(object):
    def __init__(self):
        self._updateAliasDict()

    def _updateAliasDict(self):
        self.aliases = db.Alias.getAsDict(db.getSession())

    def do_a_list(self, line):
        """List all aliases."""
        if self.aliases:
            lst = sorted(self.aliases.items(), key=lambda x: x[0])
            for name, command in lst:
                print(colors.BOLD + name.ljust(10) + colors.RESET + "=> " + command)
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
        if name in self.aliases:
            raise YokadiException("There is already an alias named {}.".format(name))
        command = " ".join(tokens[1:])

        session = db.getSession()
        db.Alias.add(session, name, command)
        session.commit()
        self._updateAliasDict()

    def do_a_edit_name(self, line):
        """Edit the name of an alias.
        a_edit_name <alias name>"""
        session = db.getSession()
        name = line
        if name not in self.aliases:
            raise YokadiException("There is no alias named {}".format(name))

        newName = tui.editLine(name)
        newName = parseOneWordName(newName)

        if newName in self.aliases:
            raise YokadiException("There is already an alias named {}.".format(newName))

        session = db.getSession()
        db.Alias.rename(session, name, newName)
        session.commit()
        self._updateAliasDict()

    def do_a_edit_command(self, line):
        """Edit the command of an alias.
        a_edit_command <alias name>"""
        session = db.getSession()
        name = line
        if name not in self.aliases:
            raise YokadiException("There is no alias named {}".format(name))

        command = tui.editLine(self.aliases[name])

        session = db.getSession()
        db.Alias.setCommand(session, name, command)
        session.commit()
        self._updateAliasDict()

    def do_a_remove(self, line):
        """Remove an alias"""
        if line in self.aliases:
            session = db.getSession()
            del self.aliases[line]
            alias = session.query(db.Alias).filter_by(name=line).one()
            session.delete(alias)
            session.commit()
        else:
            tui.error("No alias with that name. Use a_list to display all aliases")


def resolveAlias(line, aliasDict):
    """Look for alias in alias and replace it with rela command
    @param line : string to analyse
    @param aliasDict: aliases dictionnary
    @return: modified line"""
    tokens = line.split()
    if len(tokens) > 0 and tokens[0] in aliasDict:
        line = "%s %s" % (aliasDict[tokens[0]], " ".join(tokens[1:]))
    return line
