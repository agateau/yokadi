# -*- coding: UTF-8 -*-
"""
Alias related commands.

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""
from yokadi.core import db
from yokadi.core.yokadiexception import BadUsageException
from yokadi.ycli import tui
from yokadi.ycli import colors as C

from sqlalchemy.orm.exc import NoResultFound


class AliasCmd(object):
    def __init__(self):
        try:
            self.aliases = eval(db.getConfigKey(u"ALIASES", environ=False))
        except NoResultFound:
            self.aliases = {}
        except Exception:
            tui.error("Aliases syntax error. Ignored")
            self.aliases = {}

    def do_a_list(self, line):
        """List all aliases."""
        if self.aliases:
            for name, command in self.aliases.items():
                print C.BOLD + name.ljust(10) + C.RESET + "=> " + command
        else:
            print "No alias defined. Use a_add to create one"

    def do_a_add(self, line):
        """Add an alias on a command
        Ex. create an alias 'la' for 't_list -a':
        a_add la t_list -a"""
        session = db.DBHandler.getSession()
        tokens = line.split()
        if len(tokens) < 2:
            raise BadUsageException("You should provide an alias name and a command")
        name = tokens[0]
        command = " ".join(tokens[1:])
        self.aliases.update({name: command})
        try:
            aliases = session.query(db.Config).filter_by(name=u"ALIASES").one()
        except NoResultFound:
            # Config entry does not exist. Create it.
            aliases = db.Config(name=u"ALIASES", value=u"{}", system=True, desc=u"User command aliases")

        aliases.value = unicode(repr(self.aliases))
        session.add(aliases)
        session.commit()

    def do_a_remove(self, line):
        """Remove an alias"""
        if line in self.aliases:
            session = db.DBHandler.getSession()
            del self.aliases[line]
            aliases = session.query(db.Config).filter_by(name=u"ALIASES").one()
            aliases.value = unicode(repr(self.aliases))
            session.add(aliases)
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
