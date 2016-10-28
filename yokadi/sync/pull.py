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
from yokadi.sync.dump import dumpObject, checkIsValidDumpDir
from yokadi.sync.vcschanges import VcsChanges


class ChangeHandler(object):
    """
    Takes a VcsChange and apply all changes which concern `domain`

    Inherited classes can decide to defer changes to after the update to avoid
    breaking DB constraints. This can happen for example when changing project
    or task names: if two project swap names, updating them one after the other
    would cause a DB integrity failure.

    To avoid the failure, we change names to temporary names and defer changing
    names to their final value using _schedulePostUpdateChange().  Once all
    updates have been handled, scheduled changes are applied with
    applyPostUpdateChanges().
    """
    domain = None
    table = None

    def __init__(self):
        self._postUpdateChanges = []

    def handle(self, session, dumpDir, changes):
        for path in changes.added:
            if self._shouldHandleFilePath(path):
                uuid = self._getUuidFromFilePath(path)
                dct = self._loadJson(dumpDir, path)
                if self._objectExists(session, uuid):
                    # We are trying to add an object which already exists.
                    # Update it instead. This can happen when importing a
                    # complete dump in an existing database.
                    self._update(session, dct)
                else:
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
        if filePath.endswith(".json"):
            return os.path.dirname(filePath) == cls.domain
        else:
            return False

    @staticmethod
    def _loadJson(dumpDir, filePath):
        with open(os.path.join(dumpDir, filePath), "rt") as fp:
            return json.load(fp)

    @staticmethod
    def _getUuidFromFilePath(filePath):
        name = os.path.basename(filePath)
        return os.path.splitext(name)[0]

    @classmethod
    def _objectExists(cls, session, uuid):
        assert cls.table
        return dbutils.getObject(session, cls.table, uuid=uuid, _allowNone=True) is not None


class ProjectChangeHandler(ChangeHandler):
    domain = PROJECTS_DIRNAME
    table = Project

    def _add(self, session, dct):
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
    table = Task

    def _add(self, session, dct):
        task = Task()
        dbs13n.updateTaskFromDict(session, task, dct)

    def _update(self, session, dct):
        task = session.query(Task).filter_by(uuid=dct["uuid"]).one()
        dbs13n.updateTaskFromDict(session, task, dct)

    def _remove(self, session, uuid):
        session.query(Task).filter_by(uuid=uuid).delete()


class AliasChangeHandler(ChangeHandler):
    domain = ALIASES_DIRNAME
    table = Alias

    def _add(self, session, dct):
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


def _enforceProjectConstraints(session, dumpDir, pullUi):
    jsonDirPath = os.path.join(dumpDir, PROJECTS_DIRNAME)
    conflictDict = _findConflicts(jsonDirPath, "name")

    names = {x.name for x in session.query(db.Project).all()}
    for name, conflictList in conflictDict.items():
        assert len(conflictList) == 2

        # Find local project
        project = session.query(db.Project).filter_by(name=name).one()
        localUuid = project.uuid

        if conflictList[0]["uuid"] == localUuid:
            dct = conflictList[0]
        else:
            dct = conflictList[1]

        # Rename local project
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


def enforceDbConstraints(session, dumpDir, pullUi):
    # TODO: Only enforce constraints if there have been changes in the concerned
    # dir
    _enforceProjectConstraints(session, dumpDir, pullUi)
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
    checkIsValidDumpDir(dumpDir, vcsImpl)

    session = db.getSession()

    enforceDbConstraints(session, dumpDir, pullUi)
    dbConstraintChanges = vcsImpl.getWorkTreeChanges()
    changes.update(dbConstraintChanges)

    handlers = (
        ProjectChangeHandler(),
        TaskChangeHandler(),
        AliasChangeHandler()
    )
    for changeHandler in handlers:
        changeHandler.handle(session, dumpDir, changes)
    session.flush()
    for changeHandler in handlers:
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
