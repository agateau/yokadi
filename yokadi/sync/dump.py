import json
import os
import shutil

from yokadi.core import db
from yokadi.core import dbs13n
from yokadi.core.yokadiexception import YokadiException
from yokadi.core.db import Task, Project, Alias
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync import VERSION, VERSION_FILENAME, ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME, DB_SYNC_BRANCH


_TABLE_DIRNAME = (
    (Task, TASKS_DIRNAME),
    (Project, PROJECTS_DIRNAME),
    (Alias, ALIASES_DIRNAME),
)


_DIRNAME_FOR_TABLE = dict((x.__table__, y) for x, y in _TABLE_DIRNAME)


def dirnameForObject(obj):
    """Returns the dirname for obj. Can return None if this is not a serialized object,
    such as a TaskKeyword object"""
    return _DIRNAME_FOR_TABLE.get(obj.__table__)


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


def clearDump(dstDir):
    for dirname in ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME:
        path = os.path.join(dstDir, dirname)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)


def dumpObjectDict(dct, dumpDictDir):
    """Given a dict representing an object and a complete dir where to dump
    (dumpDir/$objdir), write the JSON file"""

    # dumpDir may not exist if we cloned a database which does not contain any
    # object of the type of dct (for example, no aliases)
    os.makedirs(dumpDictDir, exist_ok=True)

    uuid = dct["uuid"]
    path = os.path.join(dumpDictDir, uuid + ".json")
    with open(path, "wt") as fp:
        json.dump(dct, fp, indent=2, sort_keys=True)


def dumpProject(project, dumpDir):
    dirname = dirnameForObject(project)
    dumpDictDir = os.path.join(dumpDir, dirname)
    dct = dbs13n.dictFromProject(project)
    dumpObjectDict(dct, dumpDictDir)


def dumpTask(task, dumpDir):
    dirname = dirnameForObject(task)
    dumpDictDir = os.path.join(dumpDir, dirname)
    dct = dbs13n.dictFromTask(task)
    dumpObjectDict(dct, dumpDictDir)


def dumpAlias(alias, dumpDir):
    dirname = dirnameForObject(alias)
    dumpDictDir = os.path.join(dumpDir, dirname)
    dct = dbs13n.dictFromAlias(alias)
    dumpObjectDict(dct, dumpDictDir)


def deleteObjectDump(obj, dumpDir):
    dirname = dirnameForObject(obj)
    if dirname is None:
        return
    objPath = os.path.join(dumpDir, dirname, obj.uuid + ".json")
    if os.path.exists(objPath):
        os.unlink(objPath)


def dump(dumpDir, vcsImpl=None):
    assert os.path.exists(dumpDir)
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()
    vcsImpl.setDir(dumpDir)
    checkIsValidDumpDir(dumpDir, vcsImpl)

    session = db.getSession()
    for project in session.query(Project).all():
        dumpProject(project, dumpDir)
    for task in session.query(Task).all():
        dumpTask(task, dumpDir)
    for alias in session.query(Alias).all():
        dumpAlias(alias, dumpDir)

    if not vcsImpl.isWorkTreeClean():
        commitChanges(dumpDir, "Dumped", vcsImpl=vcsImpl)


def commitChanges(dumpDir, message, vcsImpl):
    vcsImpl.commitAll(message)
    vcsImpl.updateBranch(DB_SYNC_BRANCH, "master")
