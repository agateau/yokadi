import os

from yokadi.core import db
from yokadi.core.db import Task

from yokadi.sync.gitvcsimpl import GitVcsImpl


def getTaskUuidFromFilename(filename):
    return os.path.splitext(filename)[0]


def addTask(taskDir, filename):
    pass


def updateTask(taskDir, filename):
    uuid = getTaskUuidFromFilename(filename)
    session = db.getSession()
    task = session.query(Task).filter_by(uuid=uuid).one()


def removeTask(filename):
    uuid = getTaskUuidFromFilename(filename)
    session = db.getSession()
    session.query(Task).filter_by(uuid=uuid).delete()


def pull(dumpDir, vcsImpl=None, conflictResolver=None):
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()

    vcsImpl.setDir(dumpDir)
    commitId = vcsImpl.getCommitId()
    vcsImpl.pull()

    for conflict in vcsImpl.getConflicts():
        if not conflictResolver.resolve(conflict):
            vcsImpl.abortMerge()
            return False

    if not vcsImpl.isWorkTreeClean():
        vcsImpl.commit("Pulled")

    changes = vcsImpl.getChangesSince(commitId)
    for name in changes.added:
        addTask(dumpDir, name)
    for name in changes.modified:
        updateTask(dumpDir, name)
    for name in changes.removed:
        removeTask(name)
