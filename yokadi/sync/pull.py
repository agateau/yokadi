import json
import os

from yokadi.core import db
from yokadi.core import dbs13n
from yokadi.core.db import Task

from yokadi.sync.gitvcsimpl import GitVcsImpl


def getTaskUuidFromFilePath(filePath):
    name = os.path.basename(filePath)
    return os.path.splitext(name)[0]


def addTask(session, taskDir, filePath):
    uuid = getTaskUuidFromFilePath(filePath)
    task = Task(uuid=uuid)
    _updateTaskFromJson(task, taskDir, filePath)
    session.add(task)


def updateTask(session, taskDir, filePath):
    uuid = getTaskUuidFromFilePath(filePath)
    task = session.query(Task).filter_by(uuid=uuid).one()
    # Call session.add *before* updating, so that related objects like
    # TaskKeywords can be added to the session.
    session.add(task)
    _updateTaskFromJson(task, taskDir, filePath)


def _updateTaskFromJson(task, taskDir, filePath):
    with open(os.path.join(taskDir, filePath), "rt") as fp:
        dct = json.load(fp)
    dbs13n.updateTaskFromDict(task, dct)


def removeTask(session, filePath):
    uuid = getTaskUuidFromFilePath(filePath)
    session.query(Task).filter_by(uuid=uuid).delete()


def pull(dumpDir, vcsImpl=None, conflictResolver=None):
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()

    vcsImpl.setDir(dumpDir)
    vcsImpl.pull()

    for conflict in vcsImpl.getConflicts():
        if not conflictResolver or not conflictResolver.resolve(vcsImpl, conflict):
            vcsImpl.abortMerge()
            return False

    if not vcsImpl.isWorkTreeClean():
        vcsImpl.commitAll("Pulled")

    changes = vcsImpl.getChangesSince("synced")
    session = db.getSession()
    for path in changes.added:
        addTask(session, dumpDir, path)
    for path in changes.modified:
        updateTask(session, dumpDir, path)
    for path in changes.removed:
        removeTask(session, path)
    session.commit()

    vcsImpl.updateBranch("synced", "master")
