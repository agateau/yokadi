import os

import icalendar

from yokadi.core import db
from yokadi.core.db import Task

from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.yical import yical


def getTaskUuidFromFilename(filename):
    return os.path.splitext(filename)[0]


def addTask(session, taskDir, filename):
    uuid = getTaskUuidFromFilename(filename)
    task = Task(uuid=uuid)
    _updateTaskFromVtodo(task, taskDir, filename)
    session.add(task)


def updateTask(session, taskDir, filename):
    uuid = getTaskUuidFromFilename(filename)
    task = session.query(Task).filter_by(uuid=uuid).one()
    _updateTaskFromVtodo(task, taskDir, filename)
    session.add(task)


def _updateTaskFromVtodo(task, taskDir, filename):
    with open(os.path.join(taskDir, filename), "rt") as f:
        content = f.read()
    cal = icalendar.Calendar.from_ical(content)
    for vTodo in cal.walk():
        if "UID" in vTodo:
            yical.updateTaskFromVTodo(task, vTodo)


def removeTask(session, filename):
    uuid = getTaskUuidFromFilename(filename)
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
    for name in changes.added:
        addTask(session, dumpDir, name)
    for name in changes.modified:
        updateTask(session, dumpDir, name)
    for name in changes.removed:
        removeTask(session, name)
    session.commit()

    vcsImpl.updateBranch("synced", "master")
