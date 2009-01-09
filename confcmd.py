# -*- coding: UTF-8 -*-
"""
Configuration management related commands.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""

from db import Config
from sqlobject import AND, LIKE, SQLObjectNotFound
from yokadiexception import YokadiException
from completers import confCompleter
from textrenderer import TextRenderer
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
        try:
            k=Config.select(AND(LIKE(Config.q.name, line), Config.q.system==options.system))
            fields=[(x.name, "%s (%s)" % (x.value, x.desc)) for x in k]
            t=TextRenderer()
            t.renderFields(fields)
        except SQLObjectNotFound:
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
            p[0].value=value
            print "Parameter updated"

    complete_c_set=confCompleter
