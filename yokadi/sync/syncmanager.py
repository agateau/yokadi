import os

from yokadi.sync import VERSION, VERSION_FILENAME
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync.dump import dump
from yokadi.sync.pull import pull, importSinceLastSync, importAll


def createVersionFile(dstDir):
    versionFile = os.path.join(dstDir, VERSION_FILENAME)
    with open(versionFile, "w") as fp:
        fp.write(str(VERSION))


class SyncManager(object):
    def __init__(self, dumpDir, vcsImpl=None):
        if vcsImpl is None:
            vcsImpl = GitVcsImpl()
        self.vcsImpl = vcsImpl
        self.dumpDir = dumpDir
        self.vcsImpl.setDir(dumpDir)

    def initDumpRepository(self):
        assert not os.path.exists(self.dumpDir)
        os.makedirs(self.dumpDir)
        self.vcsImpl.init()
        createVersionFile(self.dumpDir)
        self.vcsImpl.commitAll("Created")

    def dump(self):
        dump(self.dumpDir, vcsImpl=self.vcsImpl)

    def pull(self, pullUi):
        pull(self.dumpDir, vcsImpl=self.vcsImpl, pullUi=pullUi)

    def importSinceLastSync(self, pullUi):
        importSinceLastSync(self.dumpDir, vcsImpl=self.vcsImpl, pullUi=pullUi)

    def importAll(self, pullUi):
        importAll(self.dumpDir, vcsImpl=self.vcsImpl, pullUi=pullUi)

    def push(self):
        self.vcsImpl.push()
