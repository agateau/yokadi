import json
import os

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.core import dbs13n
from yokadi.core.db import Task, Project
from yokadi.core.yokadiexception import YokadiException
from yokadi.sync import PROJECTS_DIRNAME, TASKS_DIRNAME, DB_SYNC_BRANCH
from yokadi.sync.conflictingobject import ConflictingObject
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync.pullui import PullUi


class ChangeHandler(object):
    """
    Takes a VcsChange and apply all changes which concern `domain`
    """

    domain = None
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

    def __init__(self, pullUi):
        self._pullUi = pullUi

    def _add(self, session, dct):
        # If a local project exists, update it. This will change its uuid to the
        # uuid of the remote project, resolving the conflict.
        # If there is no local project with this name, create a new one.
        project = dbutils.getProject(session, name=dct["name"], _allowNone=True)
        if project is None:
            project = Project()
        dbs13n.updateProjectFromDict(project, dct)
        session.add(project)

    def _update(self, session, dct):
        project = dbutils.getProject(session, uuid=dct["uuid"])
        existingProject = dbutils.getProject(session, name=dct["name"], _allowNone=True)
        if existingProject is not None and existingProject is not project:
            # There is already a project with this name in the database. What do
            # we do? We can either merge or rename.
            strategy = self._pullUi.getMergeStrategy(project, existingProject)
            if strategy == PullUi.MERGE:
                # Merge `project` into `existingProject`
                # Assign `project` tasks to `existingProject`
                for task in project.tasks:
                    task.project = existingProject
                session.delete(project)
                # TODO Merge `project` fields into `existingProject`
                project = existingProject
            elif strategy == PullUi.RENAME:
                # Generate a new, unique, name
                idx = 1
                name = dct["name"]
                while True:
                    dct["name"] = name + "_" + str(idx)
                    if dbutils.getProject(session, name=dct["name"], _allowNone=True) is None:
                        break
                    idx += 1
            else:
                raise YokadiException("Merge cancelled")
        assert project
        session.add(project)
        dbs13n.updateProjectFromDict(project, dct)

    def _remove(self, session, uuid):
        session.query(Project).filter_by(uuid=uuid).delete()


class TaskChangeHandler(ChangeHandler):
    domain = TASKS_DIRNAME

    def _add(self, session, dct):
        task = Task()
        dbs13n.updateTaskFromDict(task, dct)
        session.add(task)

    def _update(self, session, dct):
        task = session.query(Task).filter_by(uuid=dct["uuid"]).one()
        # Call session.add *before* updating, so that related objects like
        # TaskKeywords can be added to the session.
        session.add(task)
        dbs13n.updateTaskFromDict(task, dct)

    def _remove(self, session, uuid):
        session.query(Task).filter_by(uuid=uuid).delete()


def autoResolveConflicts(objects):
    remainingObjects = []
    for obj in objects:
        obj.autoResolve()
        if not obj.isResolved():
            remainingObjects.append(obj)
    return remainingObjects


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
        assert not vcsImpl.isWorkTreeClean()
        vcsImpl.commitAll("Merged after resolving conflicts")

    assert vcsImpl.isWorkTreeClean()

    changes = vcsImpl.getChangesSince(DB_SYNC_BRANCH)
    session = db.getSession()
    projectChangeHandler = ProjectChangeHandler(pullUi)
    taskChangeHandler = TaskChangeHandler()
    for changeHandler in projectChangeHandler, taskChangeHandler:
        changeHandler.handle(session, dumpDir, changes)
    session.commit()

    vcsImpl.updateBranch(DB_SYNC_BRANCH, "master")
