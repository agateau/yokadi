import json
import os
import shutil

from collections import defaultdict

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


def _findUniqueName(baseName, existingNames):
    name = baseName
    count = 0
    while name in existingNames:
        count += 1
        name = "{}_{}".format(baseName, count)
    return name


def _enforceAliasConstraints(dumpDir, pullUi):
    jsonDirPath = os.path.join(dumpDir, ALIASES_DIRNAME)
    dictForName = defaultdict(list)
    for name in os.listdir(jsonDirPath):
        dct = {}
        jsonPath = os.path.join(jsonDirPath, name)
        with open(jsonPath) as fp:
            dct = json.load(fp)
        dictForName[dct["name"]].append(dct)

    names = set(dictForName.keys())
    conflictLists = [x for x in dictForName.values() if len(x) > 1]
    for conflictList in conflictLists:
        ref = conflictList.pop()
        for dct in conflictList:
            if ref["command"] == dct["command"]:
                # Same command, destroy the other alias. If it was the local one
                # it will be recreated at import time.
                path = os.path.join(jsonDirPath, dct["uuid"] + ".json")
                os.remove(path)
            else:
                # Different command, rename one
                old = dct["name"]
                new = _findUniqueName(old, names)
                dct["name"] = new
                names.add(new)
                pullUi.addRename(ALIASES_DIRNAME, old, new)
                dumpObject(dct, jsonDirPath)


def enforceDbConstraints(dumpDir, pullUi):
    # TODO: Only enforce constraints if there have been changes in the concerned
    # dir
    _enforceAliasConstraints(dumpDir, pullUi)


def dump(dstDir, vcsImpl=None, pullUi=None):
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
        enforceDbConstraints(dstDir, pullUi)
        vcsImpl.commitAll()
        vcsImpl.updateBranch(DB_SYNC_BRANCH, "master")
