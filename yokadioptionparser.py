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
import sys

"""
A dummy exception which makes it possible to have --help exit silently
"""
class YokadiOptionParserNormalExitException(utils.YokadiException):
    pass

class YokadiOptionParser(OptionParser):
    def __init__(self, help=""):
        OptionParser.__init__(self)
        self.help = help

    def parse_args(self, line):
        argv = shlex.split(line.encode(utils.ENCODING))
        options, args = OptionParser.parse_args(self, argv)
        return options, [unicode(x, utils.ENCODING) for x in args]

    def exit(self, status=0, msg=None):
        if msg:
            sys.stderr.write(msg)
        if status == 0:
            raise YokadiOptionParserNormalExitException()
        else:
            raise utils.YokadiException(msg)

    def error(self, msg):
        self.print_usage(sys.stderr)
        raise utils.YokadiException(msg)

    def print_help(self, file=None):
        print self.help
# vi: ts=4 sw=4 et
