from db import *


class KeywordCmd(object):
    def do_k_list(self, line):
        """List all keywords."""
        for keyword in Keyword.select():
            print keyword.name
