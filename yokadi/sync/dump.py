import os
import shutil

import icalendar

from yokadi.core import db
from yokadi.core.yokadiexception import YokadiException
from yokadi.core.db import Task
from yokadi.yical import yical
from yokadi.sync.gitvcsimpl import GitVcsImpl


VERSION = 1
VERSION_FILENAME = "version"
PROJECTS_DIRNAME = "projects"
TASKS_DIRNAME = "tasks"


def createVersionFile(dstDir):
    versionFile = os.path.join(dstDir, VERSION_FILENAME)
    with open(versionFile, "w") as fp:
        fp.write(str(VERSION))


def checkIsValidDumpDir(dstDir, vcsImpl):
    if not vcsImpl.isValidVcsDir():
        raise YokadiException("{} is not handled by {}".format(dstDir, vcsImpl.name))

    versionFile = os.path.join(dstDir, VERSION_FILENAME)
    if not os.path.exists(versionFile):
        raise YokadiException("{} does not contain a `{}` file".format(dstDir, VERSION_FILENAME))

    with open(versionFile) as fp:
        dumpVersion = int(fp.read())
    if dumpVersion != VERSION:
        raise YokadiException("Cannot use a dump dir at version {}, expected version {}."
            .format(dumpVersion, VERSION))
    return


def rmPreviousDump(dstDir):
    for dirname in PROJECTS_DIRNAME, TASKS_DIRNAME:
        path = os.path.join(dstDir, dirname)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)


def dumpTask(task, dumpDir):
    uuid = task.uuid
    name = "{}.ics".format(uuid)
    taskPath = os.path.join(dumpDir, name)

    cal = icalendar.Calendar()
    cal.add("prodid", "-//Yokadi calendar //yokadi.github.com//")
    cal.add("version", "2.0")
    vTodo = yical.createVTodoFromTask(task)
    cal.add_component(vTodo)
    with open(taskPath, "wb") as fp:
        fp.write(cal.to_ical())


def dump(dstDir, vcsImpl=None):
    if vcsImpl == None:
        vcsImpl = GitVcsImpl()
    vcsImpl.setDir(dstDir)
    if os.path.exists(dstDir):
        checkIsValidDumpDir(dstDir, vcsImpl)
    else:
        os.makedirs(dstDir)
        vcsImpl.init()
        createVersionFile(dstDir)
        vcsImpl.commitAll("Created")

    rmPreviousDump(dstDir)
    session = db.getSession()
    tasksDir = os.path.join(dstDir, TASKS_DIRNAME)
    for task in session.query(Task).all():
        dumpTask(task, tasksDir)

    if not vcsImpl.isWorkTreeClean():
        vcsImpl.commitAll()
