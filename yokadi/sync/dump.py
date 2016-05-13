import json
import os
import shutil

from yokadi.core import db
from yokadi.core import dbs13n
from yokadi.core.yokadiexception import YokadiException
from yokadi.core.db import Task, Project, Alias
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync import VERSION, VERSION_FILENAME, ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME, DB_SYNC_BRANCH


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


def clearDump(dstDir):
    for dirname in ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME:
        path = os.path.join(dstDir, dirname)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)


def dumpObject(obj, dumpDir):
    # dumpDir may not exist if we cloned a database which does not contain any
    # object of the type of obj (for example, no aliases)
    os.makedirs(dumpDir, exist_ok=True)

    uuid = obj["uuid"]
    path = os.path.join(dumpDir, uuid + ".json")
    with open(path, "wt") as fp:
        json.dump(obj, fp, indent=2, sort_keys=True)


def dumpProject(project, dumpDir):
    dct = dbs13n.dictFromProject(project)
    dumpObject(dct, dumpDir)


def dumpTask(task, dumpDir):
    dct = dbs13n.dictFromTask(task)
    dumpObject(dct, dumpDir)


def dumpAlias(alias, dumpDir):
    dct = dbs13n.dictFromAlias(alias)
    dumpObject(dct, dumpDir)


def dump(dstDir, vcsImpl=None):
    assert os.path.exists(dstDir)
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()
    vcsImpl.setDir(dstDir)
    checkIsValidDumpDir(dstDir, vcsImpl)

    session = db.getSession()
    projectsDir = os.path.join(dstDir, PROJECTS_DIRNAME)
    for project in session.query(Project).all():
        dumpProject(project, projectsDir)
    tasksDir = os.path.join(dstDir, TASKS_DIRNAME)
    for task in session.query(Task).all():
        dumpTask(task, tasksDir)
    aliasesDir = os.path.join(dstDir, ALIASES_DIRNAME)
    for alias in session.query(Alias).all():
        dumpAlias(alias, aliasesDir)

    if not vcsImpl.isWorkTreeClean():
        vcsImpl.commitAll()
        vcsImpl.updateBranch(DB_SYNC_BRANCH, "master")
