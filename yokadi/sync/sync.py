import os
import shutil

import icalendar

from yokadi.core import db
from yokadi.core.yokadiexception import YokadiException
from yokadi.core.db import Project, Task
from yokadi.yical import yical
from yokadi.sync.gitvcsimpl import GitVcsImpl


VERSION = 1
VERSION_FILENAME = "version"
PROJECTS_DIRNAME = "projects"


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
    path = os.path.join(dstDir, PROJECTS_DIRNAME)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)


def dumpTask(task, projectPath):
    uuid = task.uuid
    name = "{}.ics".format(uuid)
    taskPath = os.path.join(projectPath, name)

    cal = icalendar.Calendar()
    cal.add("prodid", "-//Yokadi calendar //yokadi.github.com//")
    cal.add("version", "2.0")
    vTodo = yical.createVTodoFromTask(task)
    cal.add_component(vTodo)
    with open(taskPath, "wb") as fp:
        fp.write(cal.to_ical())


def dumpProjectTasks(project, dstDir):
    projectPath = os.path.join(dstDir, PROJECTS_DIRNAME, project.name)
    os.mkdir(projectPath)
    session = db.getSession()
    for task in session.query(Task).filter(Task.project==project).all():
        dumpTask(task, projectPath)


def dump(dstDir, vcsImpl=None):
    if vcsImpl == None:
        vcsImpl = GitVcsImpl()
    vcsImpl.setDir(dstDir)
    if os.path.exists(dstDir):
        checkIsValidDumpDir(dstDir, vcsImpl)
    else:
        os.makedirs(dstDir)
        createVersionFile(dstDir)
        vcsImpl.init()

    rmPreviousDump(dstDir)
    session = db.getSession()
    for project in session.query(Project).all():
        dumpProjectTasks(project, dstDir)

    if vcsImpl.hasChanges():
        vcsImpl.commit()
