# -*- coding: UTF-8 -*-
"""
Common commands. Root of all *cmd modules

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""

from parseutils import parseParameters
import re

GETLINE=re.compile("^\S+\s(.*)$")

class CommonCmd(object):
    def __init__(self):
        self.parameters=[] # Parameters given to the current running command
        self.rawline=""    # Non modified line for function that do not want default parameter parsing

    def precmd(self, line):
        # Parse parameters and store it
        m=GETLINE.match(line)
        if m:
            self.rawline=m.group(1)
        else:
            self.rawline=""
        self.parameters, line=parseParameters(line)
        return line
