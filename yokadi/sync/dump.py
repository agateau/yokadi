import json
import os
import shutil

from yokadi.core import db
from yokadi.core import dbs13n
from yokadi.core.yokadiexception import YokadiException
from yokadi.core.db import Task, Project
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync import VERSION, VERSION_FILENAME, PROJECTS_DIRNAME, TASKS_DIRNAME, DB_SYNC_BRANCH


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


def dumpProject(project, dumpDir):
    uuid = project.uuid
    name = "{}.json".format(uuid)
    projectPath = os.path.join(dumpDir, name)

    dct = dbs13n.dictFromProject(project)
    with open(projectPath, "wt") as fp:
        json.dump(dct, fp, indent=2)


def dumpTask(task, dumpDir):
    uuid = task.uuid
    name = "{}.json".format(uuid)
    taskPath = os.path.join(dumpDir, name)

    dct = dbs13n.dictFromTask(task)
    with open(taskPath, "wt") as fp:
        json.dump(dct, fp, indent=2)


def dump(dstDir, vcsImpl=None):
    assert os.path.exists(dstDir)
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()
    vcsImpl.setDir(dstDir)
    checkIsValidDumpDir(dstDir, vcsImpl)

    rmPreviousDump(dstDir)
    session = db.getSession()
    projectsDir = os.path.join(dstDir, PROJECTS_DIRNAME)
    for project in session.query(Project).all():
        dumpProject(project, projectsDir)
    tasksDir = os.path.join(dstDir, TASKS_DIRNAME)
    for task in session.query(Task).all():
        dumpTask(task, tasksDir)

    if not vcsImpl.isWorkTreeClean():
        vcsImpl.commitAll()
        vcsImpl.updateBranch(DB_SYNC_BRANCH, "master")
