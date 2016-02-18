import json
import os

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

    def _add(self, session, dct):
        project = Project()
        dbs13n.updateProjectFromDict(project, dct)
        session.add(project)

    def _update(self, session, dct):
        project = session.query(Project).filter_by(uuid=dct["uuid"]).one()
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


# Handlers must be defined in dependency order
CHANGE_HANDLERS = [
    ProjectChangeHandler(),
    TaskChangeHandler(),
]


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
    for changeHandler in CHANGE_HANDLERS:
        changeHandler.handle(session, dumpDir, changes)
    session.commit()

    vcsImpl.updateBranch("synced", "master")
