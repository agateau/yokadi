import json
import os

from sqlalchemy.orm.exc import NoResultFound

from yokadi.core import db
from yokadi.core import dbs13n
from yokadi.core.db import Task, Project
from yokadi.sync import PROJECTS_DIRNAME, TASKS_DIRNAME
from yokadi.sync.gitvcsimpl import GitVcsImpl


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

    def __init__(self, taskChangeHandler):
        self._taskChangeHandler = taskChangeHandler

    def _add(self, session, dct):
        if self._handleNameConflicts(session, dct):
            return
        project = Project()
        dbs13n.updateProjectFromDict(project, dct)
        session.add(project)

    def _update(self, session, dct):
        if self._handleNameConflicts(session, dct):
            return
        project = session.query(Project).filter_by(uuid=dct["uuid"]).one()
        session.add(project)
        dbs13n.updateProjectFromDict(project, dct)

    def _remove(self, session, uuid):
        session.query(Project).filter_by(uuid=uuid).delete()

    def _handleNameConflicts(self, session, dct):
        try:
            project = session.query(Project).filter_by(name=dct["name"]).one()
        except NoResultFound:
            # No conflicts
            return False
        self._taskChangeHandler.projectMap[dct["uuid"]] = project.uuid
        return True


class TaskChangeHandler(ChangeHandler):
    domain = TASKS_DIRNAME

    def __init__(self):
        # If remote created a project whose name is the same as a local project,
        # we do not import the remote project, instead we assign the tasks
        # associated with the remote project to the local project.
        #
        # projectMap is a dict of remoteProjectUuid => localProjectUuid. It is
        # populated by the ProjectChangeHandler
        self.projectMap = {}

    def _add(self, session, dct):
        self._applyProjectMap(dct)
        task = Task()
        dbs13n.updateTaskFromDict(task, dct)
        session.add(task)

    def _update(self, session, dct):
        self._applyProjectMap(dct)
        task = session.query(Task).filter_by(uuid=dct["uuid"]).one()
        # Call session.add *before* updating, so that related objects like
        # TaskKeywords can be added to the session.
        session.add(task)
        dbs13n.updateTaskFromDict(task, dct)

    def _remove(self, session, uuid):
        session.query(Task).filter_by(uuid=uuid).delete()

    def _applyProjectMap(self, dct):
        try:
            projectUuid = self.projectMap[dct["projectUuid"]]
        except KeyError:
            return
        dct["projectUuid"] = projectUuid


def pull(dumpDir, vcsImpl=None, conflictResolver=None):
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()

    vcsImpl.setDir(dumpDir)
    vcsImpl.pull()

    for conflict in vcsImpl.getConflicts():
        if not conflictResolver or not conflictResolver.resolve(vcsImpl, conflict):
            vcsImpl.abortMerge()
            return False

    if not vcsImpl.isWorkTreeClean():
        vcsImpl.commitAll("Pulled")

    changes = vcsImpl.getChangesSince("synced")
    session = db.getSession()
    taskChangeHandler = TaskChangeHandler()
    projectChangeHandler = ProjectChangeHandler(taskChangeHandler)
    for changeHandler in projectChangeHandler, taskChangeHandler:
        changeHandler.handle(session, dumpDir, changes)
    session.commit()

    vcsImpl.updateBranch("synced", "master")
