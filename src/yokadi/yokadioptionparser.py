# -*- coding: UTF-8 -*-
"""
An OptionParser which accepts a single string as input and raise an exception
instead of calling sys.exit() in case of error

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
from optparse import OptionParser
import sys

from yokadiexception import YokadiException

"""
A dummy exception which makes it possible to have --help exit silently
"""
class YokadiOptionParserNormalExitException(YokadiException):
    pass

class YokadiOptionParser(OptionParser):
    def __init__(self):
        OptionParser.__init__(self)

    def parse_args(self, line):
        nargv = [] # New argv with escaped arg if needed or keyword switch change
        earg = []  # Escaped argument

        argv = line.split(u" ")
        # Splitting an empty line gives us [""], not an empty array
        if argv == [u""]:
            argv = []

        # Unknown options will throw an error
        options, args =  OptionParser.parse_args(self, argv)
        return options, args


    def exit(self, status=0, msg=None):
        if msg:
            sys.stderr.write(msg)
        if status == 0:
            raise YokadiOptionParserNormalExitException()
        else:
            raise YokadiException(msg)

    def error(self, msg):
        self.print_usage(sys.stderr)
        raise YokadiException(msg)
# vi: ts=4 sw=4 et
