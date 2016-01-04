import os
from cmd import Cmd

from yokadi.core import basepaths
from yokadi.sync import dump, pull


class SyncCmd(Cmd):
    def __init__(self):
        self.dumpDir = os.path.join(basepaths.getCacheDir(), 'db')

    def do_s_dump(self, line):
        dump.dump(self.dumpDir)
        print('Database dumped in {}'.format(self.dumpDir))

    def do_s_pull(self, line):
        pull.pull(self.dumpDir)
