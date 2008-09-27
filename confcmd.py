# -*- coding: UTF-8 -*-
"""
Configuration management related commands.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""

from db import Config
from commoncmd import CommonCmd
from sqlobject import AND, LIKE, SQLObjectNotFound
from utils import YokadiException
from completers import confCompleter
import colors as C

class ConfCmd(CommonCmd):

    def do_c_get(self, line):
        """Display a configuration key. If no key is given, all keys are shown.
        Use -s switch to also display system parameters"""
        if "s" in self.parameters:
            system=True
        else:
            system=False
        if not line:
            line="%"
        try:
            k=Config.select(AND(LIKE(Config.q.name, line.strip()), Config.q.system==system))
            #TODO: a better output (using textrenderer ?) should be used !
            print "\n".join(("%-15s => %-40s (%s)" % (x.name, x.value, x.desc) for x in k))
        except SQLObjectNotFound:
            raise YokadiException("Configuration key %s does not exist" % line)

    complete_c_get=confCompleter

    def do_c_set(self, line):
        """Set a configuration key to value : c_set <key> <value>"""
        line=line.split()
        if len(line)<2:
            raise YokadiException("You should provide two arguments : the parameter key and the value")
        name=line[0]
        value=" ".join(line[1:])
        p=Config.select(AND(Config.q.name==name, Config.q.system==False))
        if p.count()==0:
            print C.RED+"Sorry, no parameter match"+C.RESET
        else:
            p[0].value=value
            print "Parameter updated"

    complete_c_set=confCompleter