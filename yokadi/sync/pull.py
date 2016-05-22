import json
import os

from collections import defaultdict

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.core import dbs13n
from yokadi.core.db import Alias, Project, Task
from yokadi.sync import ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME, DB_SYNC_BRANCH
from yokadi.sync.conflictingobject import ConflictingObject
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync.dump import dumpObject
from yokadi.sync.vcschanges import VcsChanges


class ChangeHandler(object):
    """
    Takes a VcsChange and apply all changes which concern `domain`
    """

    domain = None

    def __init__(self):
        self._postUpdateChanges = []

    def handle(self, session, dumpDir, changes):
        for path in changes.added:
            if self._shouldHandleFilePath(path):
                dct = self._loadJson(dumpDir, path)
                self._add(session, dct)
        for path in changes.modified:
            if self._shouldHandleFilePath(path):
                dct = self._loadJson(dumpDir, path)
                self._update(session, dct)
        for path in changes.removed:
            if self._shouldHandleFilePath(path):
                uuid = self._getUuidFromFilePath(path)
                self._remove(session, uuid)

    def applyPostUpdateChanges(self):
        for obj, changeDict in self._postUpdateChanges:
            for key, value in changeDict.items():
                setattr(obj, key, value)

    def _schedulePostUpdateChange(self, obj, changeDict):
        self._postUpdateChanges.append((obj, changeDict))

    def _add(self, session, dct):
        raise NotImplementedError()

    def _update(self, session, dct):
        raise NotImplementedError()

    def _remove(self, session, uuid):
        raise NotImplementedError()

    @classmethod
    def _shouldHandleFilePath(cls, filePath):
        return os.path.dirname(filePath) == cls.domain

    @staticmethod
    def _loadJson(dumpDir, filePath):
        with open(os.path.join(dumpDir, filePath), "rt") as fp:
            return json.load(fp)

    @staticmethod
    def _getUuidFromFilePath(filePath):
        name = os.path.basename(filePath)
        return os.path.splitext(name)[0]


class ProjectChangeHandler(ChangeHandler):
    domain = PROJECTS_DIRNAME

    def _add(self, session, dct):
        # If a local project exists, update it. This will change its uuid to the
        # uuid of the remote project, resolving the conflict.
        # If there is no local project with this name, create a new one.
        project = dbutils.getProject(session, name=dct["name"], _allowNone=True)
        if project is None:
            project = Project()
        self._doUpdate(session, project, dct)

    def _update(self, session, dct):
        project = dbutils.getProject(session, uuid=dct["uuid"])
        self._doUpdate(session, project, dct)

    def _doUpdate(self, session, project, dct):
        if project.name != dct["name"]:
            # Name changed, mangle it, we will set it later
            self._schedulePostUpdateChange(project, dict(name=dct["name"]))
            dct["name"] = dct["uuid"]

        dbs13n.updateProjectFromDict(project, dct)
        session.add(project)

    def _remove(self, session, uuid):
        session.query(Project).filter_by(uuid=uuid).delete()


class TaskChangeHandler(ChangeHandler):
    domain = TASKS_DIRNAME

    def _add(self, session, dct):
        # If a local task exists, update it, otherwise create a new one.
        # Updating an existing task here can happen when importing all changes
        task = dbutils.getTask(session, uuid=dct["uuid"], _allowNone=True)
        if task is None:
            task = Task()
        dbs13n.updateTaskFromDict(session, task, dct)

    def _update(self, session, dct):
        task = session.query(Task).filter_by(uuid=dct["uuid"]).one()
        dbs13n.updateTaskFromDict(session, task, dct)

    def _remove(self, session, uuid):
        session.query(Task).filter_by(uuid=uuid).delete()


class AliasChangeHandler(ChangeHandler):
    domain = ALIASES_DIRNAME

    def _add(self, session, dct):
        # If a local alias exists, update it, otherwise create a new one.
        # Updating an existing alias here can happen when importing all changes
        alias = dbutils.getAlias(session, uuid=dct["uuid"], _allowNone=True)
        if alias is None:
            alias = Alias()
        self._doUpdate(session, alias, dct)

    def _update(self, session, dct):
        alias = session.query(Alias).filter_by(uuid=dct["uuid"]).one()
        self._doUpdate(session, alias, dct)

    def _doUpdate(self, session, alias, dct):
        if alias.name != dct["name"]:
            # Name changed, mangle it, we will set it later
            self._schedulePostUpdateChange(alias, dict(name=dct["name"]))
            dct["name"] = dct["uuid"]

        dbs13n.updateAliasFromDict(alias, dct)
        session.add(alias)

    def _remove(self, session, uuid):
        session.query(Alias).filter_by(uuid=uuid).delete()


def autoResolveConflicts(objects):
    remainingObjects = []
    for obj in objects:
        obj.autoResolve()
        if not obj.isResolved():
            remainingObjects.append(obj)
    return remainingObjects


def _findUniqueName(baseName, existingNames):
    name = baseName
    count = 0
    while name in existingNames:
        count += 1
        name = "{}_{}".format(baseName, count)
    return name


def _findConflicts(jsonDirPath, fieldName):
    """
    Returns a dict of the form
            fieldValue => [{dct1}, {dct2}]
    ],
    """
    if not os.path.exists(jsonDirPath):
        return {}
    dictForField = defaultdict(list)
    for name in os.listdir(jsonDirPath):
        jsonPath = os.path.join(jsonDirPath, name)
        with open(jsonPath) as fp:
            dct = json.load(fp)
        fieldValue = dct[fieldName]
        dictForField[fieldValue].append(dct)

    return {k: v for k, v in dictForField.items() if len(v) > 1}


def _enforceProjectConstraints(dumpDir, pullUi):
    jsonDirPath = os.path.join(dumpDir, PROJECTS_DIRNAME)
    conflictDict = _findConflicts(jsonDirPath, "name")

    names = set(conflictDict.keys())
    for conflictList in conflictDict.values():
        ref = conflictList.pop()
        for dct in conflictList:
            old = dct["name"]
            new = _findUniqueName(old, names)
            dct["name"] = new
            names.add(new)
            pullUi.addRename(PROJECTS_DIRNAME, old, new)
            dumpObject(dct, jsonDirPath)


def _enforceAliasConstraints(dumpDir, pullUi):
    jsonDirPath = os.path.join(dumpDir, ALIASES_DIRNAME)
    conflictDict = _findConflicts(jsonDirPath, "name")

    names = set(conflictDict.keys())
    for conflictList in conflictDict.values():
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
    _enforceProjectConstraints(dumpDir, pullUi)
    _enforceAliasConstraints(dumpDir, pullUi)


def importSinceLastSync(dumpDir, vcsImpl=None, pullUi=None):
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()
    vcsImpl.setDir(dumpDir)
    assert vcsImpl.isWorkTreeClean()
    changes = vcsImpl.getChangesSince(DB_SYNC_BRANCH)
    _importChanges(dumpDir, changes, vcsImpl=vcsImpl, pullUi=pullUi)


def importAll(dumpDir, vcsImpl=None, pullUi=None):
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()
    vcsImpl.setDir(dumpDir)
    assert vcsImpl.isWorkTreeClean()
    changes = VcsChanges()
    changes.added = {x for x in vcsImpl.getTrackedFiles() if x.endswith(".json")}
    _importChanges(dumpDir, changes, vcsImpl=vcsImpl, pullUi=pullUi)


def _importChanges(dumpDir, changes, vcsImpl=None, pullUi=None):
    session = db.getSession()

    enforceDbConstraints(dumpDir, pullUi)
    dbConstraintChanges = vcsImpl.getWorkTreeChanges()
    changes.update(dbConstraintChanges)

    projectChangeHandler = ProjectChangeHandler()
    taskChangeHandler = TaskChangeHandler()
    aliasChangeHandler = AliasChangeHandler()
    for changeHandler in projectChangeHandler, taskChangeHandler, aliasChangeHandler:
        changeHandler.handle(session, dumpDir, changes)
    session.flush()
    for changeHandler in projectChangeHandler, taskChangeHandler, aliasChangeHandler:
        changeHandler.applyPostUpdateChanges()
    session.commit()

    if dbConstraintChanges.hasChanges():
        # Only commit after the DB session has been committed, to be able to
        # rollback both the DB and the repository in case of error
        vcsImpl.commitAll("Enforce DB constraints")

    vcsImpl.updateBranch(DB_SYNC_BRANCH, "master")


def pull(dumpDir, vcsImpl=None, pullUi=None):
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()

    vcsImpl.setDir(dumpDir)
    assert vcsImpl.isWorkTreeClean()
    vcsImpl.pull()

    if vcsImpl.hasConflicts():
        objects = [ConflictingObject.fromVcsConflict(x) for x in vcsImpl.getConflicts()]
        remainingObjects = autoResolveConflicts(objects)
        if remainingObjects:
            pullUi.resolveConflicts(remainingObjects)

        for obj in objects:
            if obj.isResolved():
                obj.close(vcsImpl)
            else:
                vcsImpl.abortMerge()
                return False

        assert not vcsImpl.hasConflicts()

    if not vcsImpl.isWorkTreeClean():
        vcsImpl.commitAll("Merged")

    assert vcsImpl.isWorkTreeClean()
    return True
