# -*- coding: UTF-8 -*-
"""
Keyword related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
from db import *


class KeywordCmd(object):
    def do_k_list(self, line):
        """List all keywords."""
        for keyword in Keyword.select():
            tasks=", ".join(str(task.id) for task in keyword.tasks)
            print "%s (tasks: %s)" % (keyword.name, tasks)
