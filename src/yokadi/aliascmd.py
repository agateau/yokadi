# -*- coding: UTF-8 -*-
"""
Alias related commands.

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""
from db import Config
from yokadiexception import YokadiException
import tui
import colors as C

from sqlobject import SQLObjectNotFound

class AliasCmd(object):
    def __init__(self):
        try:
            self.aliases = eval(Config.byName("ALIASES").value)
        except SQLObjectNotFound:
            self.aliases = {}
        except Exception, e:
            tui.error("Aliases syntax error. Ignored")
            self.aliases = {}

    def do_a_list(self, line):
        """List all aliases."""
        if self.aliases:
            for name, command in self.aliases.items():
                print C.BOLD+name.ljust(10) + C.RESET + "=> " + command
        else:
            print "No alias defined. Use a_add to create one"

    def do_a_add(self, line):
        """Add an alias on a command
        Ex. create an alias 'la' for 't_list -a':
        a_add la t_list -a"""
        tokens = line.split()
        if len(tokens)<2:
            raise YokadiException("You should provide an alias name and a command")
        name=tokens[0]
        command=" ".join(tokens[1:])
        self.aliases.update({ name : command})
        try:
            aliases = Config.selectBy(name="ALIASES")[0]
        except IndexError:
            # Config entry does not exist. Create it.
            aliases = Config(name="ALIASES", value="{}", system=True, desc="User command aliases")

        aliases.value = repr(self.aliases)

    def do_a_remove(self, line):
        """Remove an alias"""
        if line in self.aliases:
            del self.aliases[line]
            aliases = Config.selectBy(name="ALIASES")[0]
            aliases.value = repr(self.aliases)
        else:
            tui.error("No alias with that name. Use a_list to display all aliases")

def resolveAlias(line, aliasDict):
    """Look for alias in alias and replace it with rela command
    @param line : string to analyse
    @param aliasDict: aliases dictionnary
    @return: modified line"""
    tokens = line.split()
    if len(tokens)>0 and tokens[0] in aliasDict:
        line = "%s %s" % (aliasDict[tokens[0]], " ".join(tokens[1:]))
    return line
