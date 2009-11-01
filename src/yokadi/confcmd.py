# -*- coding: UTF-8 -*-
"""
Configuration management related commands.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""

from db import Config
from sqlobject import AND, LIKE, SQLObjectNotFound
from yokadiexception import YokadiException
from completers import confCompleter
import tui
from yokadioptionparser import YokadiOptionParser

class ConfCmd(object):

    def parser_c_get(self):
        parser = YokadiOptionParser()
        parser.set_usage("c_get [options] [<key>]")
        parser.set_description("Display the value of a configuration key. If no key is given, all keys are shown.")
        parser.add_option("-s", dest="system", default=False, action="store_true",
                          help="Display value of system keys instead of user ones")
        return parser

    def do_c_get(self, line):
        parser = self.parser_c_get()
        options, args = parser.parse_args(line)
        line = u" ".join(args)
        if not line:
            line="%"
        k=Config.select(AND(LIKE(Config.q.name, line), Config.q.system==options.system))
        fields=[(x.name, "%s (%s)" % (x.value, x.desc)) for x in k]
        if fields:
            tui.renderFields(fields)
        else:
            raise YokadiException("Configuration key %s does not exist" % line)

    complete_c_get=confCompleter

    def do_c_set(self, line):
        """Set a configuration key to value : c_set <key> <value>"""
        line=line.split()
        if len(line)<2:
            raise YokadiException("You should provide two arguments : the parameter key and the value")
        name=line[0]
        value=" ".join(line[1:])
        p=Config.select(AND(Config.q.name==name, Config.q.system==False))
        if p.count()==0:
            tui.error("Sorry, no parameter match")
        else:
            if self.checkParameterValue(name, value):
                p[0].value=value
                tui.info("Parameter updated")
            else:
                tui.error("Parameter value is incorrect")

    complete_c_set=confCompleter

    def checkParameterValue(self, name, value):
        """Control that the value if ok for a parameter
        @param key: parameter name
        @param value: parameter value
        @return: True if parameter is ok, else False"""
        # Positive int parameters
        if name in ("ALARM_DELAY", "ALARM_SUSPEND", "PURGE_DELAY"):
            try:
                value=int(value)
                assert(value>=0)
                return True
            except (ValueError, AssertionError):
                return False
        else:
            # No check for this parameter, so tell everything is fine
            return True