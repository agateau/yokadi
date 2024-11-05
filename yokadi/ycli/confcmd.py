# -*- coding: UTF-8 -*-
"""
Configuration management related commands.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
from yokadi.core import db

from yokadi.core.db import Config
from yokadi.core.yokadiexception import YokadiException, BadUsageException
from yokadi.ycli.completers import confCompleter
from yokadi.ycli import tui
from yokadi.core.yokadioptionparser import YokadiOptionParser


class ConfCmd(object):
    def parser_c_get(self):
        parser = YokadiOptionParser(prog="c_get")
        parser.description = "Display the value of a configuration key. If no key is given, all keys are shown."
        parser.add_argument("-s", dest="system", default=False, action="store_true",
                            help="Display value of system keys instead of user ones")
        parser.add_argument("key", nargs='?')
        return parser

    def do_c_get(self, line):
        parser = self.parser_c_get()
        args = parser.parse_args(line)
        key = args.key
        if not key:
            key = "%"
        session = db.getSession()
        k = session.query(Config).filter(Config.name.like(key)).filter_by(system=args.system).all()
        fields = [(x.name, "%s (%s)" % (x.value, x.desc)) for x in k]
        if fields:
            tui.renderFields(fields)
        else:
            raise YokadiException("Configuration key %s does not exist" % line)

    complete_c_get = confCompleter

    def do_c_set(self, line):
        """Set a configuration key to value : c_set <key> <value>"""
        line = line.split()
        if len(line) < 2:
            raise BadUsageException("You should provide two arguments : the parameter key and the value")
        name = line[0]
        value = " ".join(line[1:])
        session = db.getSession()
        p = session.query(Config).filter_by(name=name, system=False)
        if p.count() == 0:
            raise YokadiException("Sorry, no parameter match")
        else:
            if self.checkParameterValue(name, value):
                p[0].value = value
                tui.info("Parameter updated")
            else:
                raise YokadiException("Parameter value is incorrect")

    complete_c_set = confCompleter

    def checkParameterValue(self, name, value):
        """Control that the value if ok for a parameter
        @param key: parameter name
        @param value: parameter value
        @return: True if parameter is ok, else False"""
        # Positive int parameters
        if name in ("ALARM_DELAY", "ALARM_SUSPEND", "PURGE_DELAY"):
            try:
                value = int(value)
                assert value >= 0
                return True
            except (ValueError, AssertionError):
                return False
        else:
            # No check for this parameter, so tell everything is fine
            return True
