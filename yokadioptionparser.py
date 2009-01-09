# -*- coding: UTF-8 -*-
"""
An OptionParser which accepts a single string as input and raise an exception
instead of calling sys.exit() in case of error

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
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
        argv = line.split(u" ")
        # Splitting an empty line gives us [""], not an empty array
        if argv == [u""]:
            argv = []
        # Escape things that looks like arg but are indeed value (a user text with a dash for example)
        nargv = [] # New argv with escaped arg if needed
        earg = []  # Escaped argument
        for arg in argv:
            if self.get_option(arg):
                nargv.append(arg)
            else:
                arg=arg.replace("-", "\-")
                earg.append(arg)
                nargv.append(arg)

        options, args =  OptionParser.parse_args(self, nargv)

        # Now, remove escaping
        nargs=[] # New args with escaping removed
        for arg in args:
            if arg in earg:
                nargs.append(arg.replace("\-", "-"))
            else:
                nargs.append(arg)
        return options, nargs


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
