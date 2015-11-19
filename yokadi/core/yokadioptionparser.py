# -*- coding: UTF-8 -*-
"""
An ArgumentParser which accepts a single string as input and raise an exception
instead of calling sys.exit() in case of error

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from argparse import ArgumentParser
import sys

from yokadi.core.yokadiexception import YokadiException


class YokadiOptionParserNormalExitException(YokadiException):
    """A dummy exception which makes it possible to have --help exit silently"""
    pass


class YokadiOptionParser(ArgumentParser):
    def __init__(self, prog=None):
        ArgumentParser.__init__(self, prog=prog)

    def parse_args(self, line):
        argv = line.split(" ")
        # Splitting an empty line gives us [""], not an empty array
        if argv == [""]:
            argv = []

        # Unknown options will throw an error
        args = ArgumentParser.parse_args(self, argv)
        return args

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
