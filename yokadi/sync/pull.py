"""
Functions to import changes from the dump dir to the database

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import json
import os

from collections import defaultdict

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.core import dbs13n
from yokadi.core.db import Alias, Project, Task
from yokadi.sync import ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME
from yokadi.sync.conflictingobject import ConflictingObject
from yokadi.sync.dump import dumpObjectDict, checkIsValidDumpDir
from yokadi.sync.syncerrors import MergeError
from yokadi.sync.vcschanges import VcsChanges


class PullError(Exception):
    pass


class ChangeHandler(object):
    """
    Takes a VcsChange and apply all changes which concern `domain`

    Inherited classes can decide to defer changes to after the update to avoid
    breaking DB constraints. This can happen for example when changing project
    or alias names: if two project swap names, updating them one after the
    other would cause a DB integrity failure.

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
        for path in changes.added | changes.modified:
            if self._shouldHandleFilePath(path):
                try:
                    dct = self._loadJson(dumpDir, path)
                    obj = self._loadObject(session, dct["uuid"])
                    self._update(session, obj, dct)
                except Exception as exc:
                    raise PullError("Error while adding {}".format(path)) from exc
        for path in changes.removed:
            if self._shouldHandleFilePath(path):
                uuid = self._getUuidFromFilePath(path)
                try:
                    self._remove(session, uuid)
                except Exception as exc:
                    raise PullError("Error while removing {}".format(path)) from exc

    def applyPostUpdateChanges(self):
        for obj, changeDict in self._postUpdateChanges:
            for key, value in changeDict.items():
                setattr(obj, key, value)

    def _schedulePostUpdateChange(self, obj, changeDict):
        self._postUpdateChanges.append((obj, changeDict))

    def _update(self, session, obj, dct):
        """Must update the object `obj` with the values of dict `dct`
        """
        raise NotImplementedError()

    def _remove(self, session, uuid):
        session.query(self.table).filter_by(uuid=uuid).delete()

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
    def _loadObject(cls, session, uuid):
        assert cls.table
        obj = dbutils.getObject(session, cls.table, uuid=uuid, _allowNone=True)
        if not obj:
            obj = cls.table()
        return obj


class ProjectChangeHandler(ChangeHandler):
    domain = PROJECTS_DIRNAME
    table = Project

    def _update(self, session, project, dct):
        if project.name != dct["name"]:
            # Name changed, mangle it, we will set it later
            self._schedulePostUpdateChange(project, dict(name=dct["name"]))
            dct["name"] = dct["uuid"]

        dbs13n.updateProjectFromDict(session, project, dct)


class TaskChangeHandler(ChangeHandler):
    domain = TASKS_DIRNAME
    table = Task

    def _update(self, session, task, dct):
        dbs13n.updateTaskFromDict(session, task, dct)


class AliasChangeHandler(ChangeHandler):
    domain = ALIASES_DIRNAME
    table = Alias

    def _update(self, session, alias, dct):
        if alias.name != dct["name"]:
            # Name changed, mangle it, we will set it later
            self._schedulePostUpdateChange(alias, dict(name=dct["name"]))
            dct["name"] = dct["uuid"]

        dbs13n.updateAliasFromDict(session, alias, dct)


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


def findConflicts(jsonDirPath, fieldName):
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
    conflictDict = findConflicts(jsonDirPath, "name")

    names = {x.name for x in session.query(db.Project).all()}
    for name, conflictList in conflictDict.items():
        assert len(conflictList) == 2, "More than 2 projects are named '{}', this should not happen! (uuids: {})" \
                                       .format(name, [x["uuid"] for x in conflictList])

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
        dumpObjectDict(dct, jsonDirPath)


def _enforceAliasConstraints(session, dumpDir, pullUi):
    jsonDirPath = os.path.join(dumpDir, ALIASES_DIRNAME)
    conflictDict = findConflicts(jsonDirPath, "name")

    names = {x.name for x in session.query(db.Alias).all()}
    for name, conflictList in conflictDict.items():
        assert len(conflictList) == 2, "More than 2 aliases are named '{}', this should not happen! (uuids: {})" \
                                       .format(name, [x["uuid"] for x in conflictList])

        # Find local alias
        alias = session.query(db.Alias).filter_by(name=name).one()
        localUuid = alias.uuid

        if conflictList[0]["uuid"] == localUuid:
            local, remote = conflictList[0], conflictList[1]
        else:
            local, remote = conflictList[1], conflictList[0]

        if local["command"] == remote["command"]:
            # Same command, destroy dump of local alias
            objPath = os.path.join(jsonDirPath, localUuid + '.json')
            assert os.path.exists(objPath), "{} does not exist".format(objPath)
            os.unlink(objPath)
        else:
            # Different command, rename local alias
            old = alias.name
            new = _findUniqueName(old, names)
            pullUi.addRename(ALIASES_DIRNAME, old, new)
            local["name"] = new
            dumpObjectDict(local, jsonDirPath)


def enforceDbConstraints(session, dumpDir, pullUi):
    # TODO: Only enforce constraints if there have been changes in the concerned
    # dir
    _enforceProjectConstraints(session, dumpDir, pullUi)
    _enforceAliasConstraints(session, dumpDir, pullUi)


def importSince(vcsImpl, commitId, pullUi=None):
    assert vcsImpl.isWorkTreeClean(), "Git repository in {} is not clean".format(vcsImpl.srcDir)
    changes = vcsImpl.getChangesSince(commitId)
    _importChanges(vcsImpl, changes, pullUi=pullUi)


def importAll(vcsImpl, pullUi=None):
    assert vcsImpl.isWorkTreeClean(), "Git repository in {} is not clean".format(vcsImpl.srcDir)
    changes = VcsChanges()
    changes.added = {x for x in vcsImpl.getTrackedFiles() if x.endswith(".json")}
    _importChanges(vcsImpl, changes, pullUi=pullUi)


def _importChanges(vcsImpl, changes, pullUi=None):
    checkIsValidDumpDir(vcsImpl)

    session = db.getSession()

    enforceDbConstraints(session, vcsImpl.srcDir, pullUi)
    dbConstraintChanges = vcsImpl.getWorkTreeChanges()
    changes.update(dbConstraintChanges)

    handlers = (
        ProjectChangeHandler(),
        TaskChangeHandler(),
        AliasChangeHandler()
    )
    for changeHandler in handlers:
        changeHandler.handle(session, vcsImpl.srcDir, changes)
    session.flush()
    for changeHandler in handlers:
        changeHandler.applyPostUpdateChanges()
    session.commit()

    if not vcsImpl.isWorkTreeClean():
        # Only commit after the DB session has been committed, to be able to
        # rollback both the DB and the repository in case of error
        vcsImpl.commitAll("Enforce DB constraints")


def merge(vcsImpl, pullUi=None):
    dumpDir = vcsImpl.srcDir
    assert vcsImpl.isWorkTreeClean(), "Git repository in {} is not clean".format(dumpDir)
    vcsImpl.merge()

    if vcsImpl.hasConflicts():
        objects = [ConflictingObject.fromVcsConflict(x) for x in vcsImpl.getConflicts()]
        remainingObjects = autoResolveConflicts(objects)
        if remainingObjects:
            pullUi.resolveConflicts(remainingObjects)

        for obj in objects:
            if obj.isResolved():
                obj.close(vcsImpl)
            else:
                raise MergeError("Unsolved conflict on {}".format(obj))

        assert not vcsImpl.hasConflicts(), "There are still conflicts in {}".format(dumpDir)

    if not vcsImpl.isWorkTreeClean():
        vcsImpl.commitAll("Merged")

    assert vcsImpl.isWorkTreeClean(), "Git repository in {} is not clean".format(dumpDir)
