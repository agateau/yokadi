# -*- coding: UTF-8 -*-
"""
An OptionParser which accepts a single string as input and raise an exception
instead of calling sys.exit() in case of error

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
from optparse import OptionParser
import shlex

class YokadiOptionParser(OptionParser):
    def parse_args(self, line):
        args = shlex.split(line.encode("utf-8"))
        return OptionParser.parse_args(self, args)

    def error(self):
        raise YokadiException("Parse error")
# vi: ts=4 sw=4 et
