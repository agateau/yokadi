# -*- coding: UTF-8 -*-
"""
Configuration management related commands.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""

from db import Config
from sqlobject import LIKE, SQLObjectNotFound
from utils import YokadiException

class ConfCmd(object):
    
    def do_c_get(self, line):
        """Display a configuration key. If no key is given, all keys are shown"""
        if not line:
            line="%"
        try:
            k=Config.select(LIKE(Config.q.name, line))
            #TODO: a better output (using textrenderer ?) should be used !
            print "\n".join(("%s => %s" % (x.name, x.value) for x in k))
        except SQLObjectNotFound:
            raise YokadiException("Configuration key %s does not exist" % line)