# -*- coding: UTF-8 -*-
"""
An OptionParser which accepts a single string as input and raise an exception
instead of calling sys.exit() in case of error

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
from optparse import OptionParser
import shlex
import utils

class YokadiOptionParser(OptionParser):
    def parse_args(self, line):
        argv = shlex.split(line.encode(utils.ENCODING))
        options, args = OptionParser.parse_args(self, argv)
        return options, [unicode(x, utils.ENCODING) for x in args]

    def error(self):
        raise YokadiException("Parse error")
# vi: ts=4 sw=4 et
