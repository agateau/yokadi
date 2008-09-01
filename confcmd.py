# -*- coding: UTF-8 -*-
"""
Configuration management related commands.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""

from db import Config
from sqlobject import AND, LIKE, SQLObjectNotFound
from utils import YokadiException
import colors as C

class ConfCmd(object):

    def do_c_get(self, line):
        """Display a configuration key. If no key is given, all keys are shown.
        Use -s switch to also display system parameters"""
        if "-s" in line:
            line=line.strip("-s")
            system=True
        else:
            system=False
        if not line:
            line="%"
        try:
            k=Config.select(AND(LIKE(Config.q.name, line.strip()), Config.q.system==system))
            #TODO: a better output (using textrenderer ?) should be used !
            print "\n".join(("%s => %s" % (x.name, x.value) for x in k))
        except SQLObjectNotFound:
            raise YokadiException("Configuration key %s does not exist" % line)

    def do_c_set(self, line):
        """Set a configuration key to value : c_set <key> <value>"""
        line=line.split()
        if len(line)!=2:
            raise YokadiException("You should provide two arguments : the parameter key and the value")
        name, value=line
        p=Config.select(AND(Config.q.name==name, Config.q.system==False))
        if p.count()==0:
            print C.RED+"Sorry, no parameter match"+C.RESET
        else:
            p[0].value=value
            print "Parameter updated"