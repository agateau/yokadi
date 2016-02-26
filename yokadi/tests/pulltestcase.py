import json
import os
import unittest

from tempfile import TemporaryDirectory

from yokadi.core import db, dbutils
from yokadi.core.db import Task, Project
from yokadi.sync import PROJECTS_DIRNAME, TASKS_DIRNAME
from yokadi.sync.pull import pull
from yokadi.sync.pullui import PullUi
from yokadi.sync.vcschanges import VcsChanges


class StubVcsImpl(object):
    def setDir(self, repoDir):
        pass

    def pull(self):
        pass

    def hasConflicts(self):
        return bool(self.getConflicts())

    def getConflicts(self):
        return []

    def isWorkTreeClean(self):
        return True

    def commitAll(message=""):
        pass

    def getChangesSince(self, commitId):
        return VcsChanges()

    def updateBranch(self, branch, commitId):
        pass


def createProjectFile(dirname, uuid, name, active=True):
    projectDir = os.path.join(dirname, PROJECTS_DIRNAME)
    if not os.path.exists(projectDir):
        os.mkdir(projectDir)
    dct = {
        "uuid": uuid,
        "name": name,
        "active": active,
    }
    filePath = os.path.join(projectDir, uuid + ".json")
    with open(filePath, "wt") as fp:
        json.dump(dct, fp)
    return os.path.relpath(filePath, dirname)


def createTaskFile(dirname, uuid, projectUuid, title, **kwargs):
    taskDir = os.path.join(dirname, TASKS_DIRNAME)
    if not os.path.exists(taskDir):
        os.mkdir(taskDir)
    dct = {
        "projectUuid": projectUuid,
        "uuid": uuid,
        "title": title,
        "creationDate": "2016-01-12T19:12:00",
        "keywords": {},
    }
    dct.update(kwargs)
    filePath = os.path.join(taskDir, uuid + ".json")
    with open(filePath, "wt") as fp:
        json.dump(dct, fp)
    return os.path.relpath(filePath, dirname)


class PullTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

    def testNothingToDo(self):
        with TemporaryDirectory() as tmpDir:
            vcsImpl = StubVcsImpl()
            pull(tmpDir, vcsImpl)

    def testRemoteChangesOnly(self):
        with TemporaryDirectory() as tmpDir:
            # Create two tasks, one which will be modified and one which will be
            # removed
            prj = dbutils.getOrCreateProject("prj", interactive=False)

            modifiedTask = dbutils.addTask("prj", "Modified", interactive=False)
            modifiedTask.uuid = "1234-modified"
            self.session.add(modifiedTask)
            dbutils.createMissingKeywords(("kw1", "kw2"), interactive=False)
            modifiedTask.setKeywordDict(dict(kw1=None, kw2=2))

            removedTask = dbutils.addTask("prj", "Removed", interactive=False)
            removedTask.uuid = "1234-removed"
            self.session.add(removedTask)
            self.session.commit()

            # Prepare a fake vcs pull: create files which would result from the
            # pull and create a VcsImpl to fake it
            addedProjectPath = createProjectFile(
                    tmpDir,
                    name="prj2",
                    uuid="5678-prj2")
            addedTaskPath = createTaskFile(
                    tmpDir,
                    uuid="1234-added",
                    projectUuid=prj.uuid,
                    title="Added")
            modifiedTaskPath = createTaskFile(
                    tmpDir,
                    uuid="1234-modified",
                    projectUuid="5678-prj2",
                    title="New task title",
                    keywords=dict(kw1=None, kw2=2))
            removedTaskPath = os.path.join(TASKS_DIRNAME, removedTask.uuid + ".json")

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.added = {addedProjectPath, addedTaskPath}
                    changes.modified = {modifiedTaskPath}
                    changes.removed = {removedTaskPath}
                    return changes

            # Do the pull
            pull(tmpDir, MyVcsImpl())

            # Check changes
            modifiedTask2 = dbutils.getTaskFromId(modifiedTask.id)
            self.assertEqual(modifiedTask2.project.name, "prj2")
            self.assertEqual(modifiedTask2.title, "New task title")

            addedTask = self.session.query(Task).filter_by(uuid="1234-added").one()
            self.assertEqual(addedTask.project.name, "prj")
            self.assertEqual(addedTask.title, "Added")

            lst = self.session.query(Task).filter_by(id=removedTask.id)
            self.assertEqual(len(list(lst)), 0)

    def testRemoteAndLocalChanges(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            self.session.commit()

            # Prepare a fake vcs pull: create an added file
            # and create a VcsImpl to fake it
            addedTaskPath = createTaskFile(
                    tmpDir,
                    uuid="1234-added",
                    projectUuid=prj.uuid,
                    title="Added")

            class MyVcsImpl(StubVcsImpl):
                def __init__(self):
                    self.commitAllCallCount = 0

                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.added = {addedTaskPath}
                    return changes

                def isWorkTreeClean(self):
                    return False

                def commitAll(self, message=""):
                    self.commitAllCallCount += 1

            # Do the pull
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl)

            # Check changes. Since work tree was not clean there should be a
            # commit to finish the merge.
            self.assertEqual(vcsImpl.commitAllCallCount, 1)

            addedTask = self.session.query(Task).filter_by(uuid="1234-added").one()
            self.assertEqual(addedTask.project.name, "prj")
            self.assertEqual(addedTask.title, "Added")

    def testConflictsAbortMerge(self):
        with TemporaryDirectory() as tmpDir:
            class MyVcsImpl(StubVcsImpl):
                def __init__(self):
                    self.abortMergeCallCount = 0
                    self.commitAllCallCount = 0

                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.added = {"1234-conflict.json"}
                    return changes

                def isWorkTreeClean(self):
                    return False

                def getConflicts(self):
                    return [(b'UU', '1234-conflict.json')]

                def abortMerge(self):
                    self.abortMergeCallCount += 1

                def commitAll(self, message=""):
                    self.commitAllCallCount += 1

            # Do the pull
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl)

            # Check changes. Since there was a conflict there should be no
            # commit.
            self.assertEqual(vcsImpl.abortMergeCallCount, 1)
            self.assertEqual(vcsImpl.commitAllCallCount, 0)

    def testConflictsSolved(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)

            modifiedTask = dbutils.addTask("prj", "Local title", interactive=False)
            modifiedTask.uuid = "1234-conflict"
            self.session.add(modifiedTask)

            modifiedTaskPath = createTaskFile(
                    tmpDir,
                    uuid=modifiedTask.uuid,
                    projectUuid=prj.uuid,
                    title="Remote title")

            class MyPullUi(PullUi):
                def resolveConflicts(self, vcsImpl):
                    vcsImpl.conflicts = []

            class MyVcsImpl(StubVcsImpl):
                def __init__(self):
                    self.abortMergeCallCount = 0
                    self.commitAllCallCount = 0
                    self.conflicts = [(b'UU', modifiedTaskPath)]

                def getChangesSince(self, commitId):
                    # This is called after the conflict has been resolved, so it
                    # must return the task as modified
                    changes = VcsChanges()
                    changes.modified = {modifiedTaskPath}
                    return changes

                def isWorkTreeClean(self):
                    return False

                def getConflicts(self):
                    return self.conflicts

                def abortMerge(self):
                    self.abortMergeCallCount += 1

                def commitAll(self, message=""):
                    self.commitAllCallCount += 1

            # Do the pull
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl=vcsImpl, pullUi=MyPullUi())

            # Check changes. Conflict has been solved, there should be a merge.
            self.assertEqual(vcsImpl.abortMergeCallCount, 0)
            self.assertEqual(vcsImpl.commitAllCallCount, 1)

            modifiedTask2 = dbutils.getTaskFromId(modifiedTask.id)
            self.assertEqual(modifiedTask2.title, "Remote title")

    def testProjectUpdated(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            self.session.commit()

            modifiedProjectPath = createProjectFile(
                    tmpDir,
                    name="prj2",
                    uuid=prj.uuid)

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.modified = {modifiedProjectPath}
                    return changes

            # Do the pull
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl=vcsImpl)

            # Check changes
            prj2 = self.session.query(Project).filter_by(id=prj.id).one()
            self.assertEqual(prj2.name, "prj2")

    def testProjectRemoved(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            task = dbutils.addTask(prj.name, "title", interactive=False)
            self.session.commit()

            removedProjectPath = os.path.join(PROJECTS_DIRNAME, prj.uuid + ".json")
            removedTaskPath = os.path.join(TASKS_DIRNAME, task.uuid + ".json")

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.removed = {removedProjectPath, removedTaskPath}
                    return changes

            # Do the pull
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl=vcsImpl)

            # DB should be empty
            projects = self.session.query(Project).all()
            self.assertEqual(len(list(projects)), 0)
            tasks = self.session.query(Task).all()
            self.assertEqual(len(list(tasks)), 0)

    def testRemoteCreateSameProject(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            task1 = dbutils.addTask(prj.name, "task1", interactive=False)
            self.session.commit()

            addedProjectPath = createProjectFile(
                    tmpDir,
                    name="prj",
                    uuid="5678-prj2")
            addedTaskPath = createTaskFile(
                    tmpDir,
                    title="task2",
                    projectUuid="5678-prj2",
                    uuid="1234-task")

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.added = {addedProjectPath, addedTaskPath}
                    return changes

            # Do the pull
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl=vcsImpl)

            # The added project should not be there, task2 should be in prj
            projects = list(self.session.query(Project).all())
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0].uuid, prj.uuid)

            tasks = list(self.session.query(Task).all())
            self.assertEqual(len(tasks), 2)
            task2 = self.session.query(Task).filter_by(uuid="1234-task").one()
            self.assertEqual(task2.project.uuid, prj.uuid)

    def testRemoteRenamedProject(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            task1 = dbutils.addTask(prj.name, "task1", interactive=False)
            self.session.commit()

            renamedProjectPath = createProjectFile(
                    tmpDir,
                    name="prj2",
                    uuid=prj.uuid)

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.modified = {renamedProjectPath}
                    return changes

            # Do the pull
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl=vcsImpl)

            # The project should have a new name, task1 should still be there
            projects = list(self.session.query(Project).all())
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0].uuid, prj.uuid)
            self.assertEqual(projects[0].name, "prj2")

            tasks = list(self.session.query(Task).all())
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].project.uuid, prj.uuid)
            self.assertEqual(tasks[0].title, task1.title)

    def testRemoteRenamedProjectLikeLocalProject_merge(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            prj2 = dbutils.getOrCreateProject("prj2", interactive=False)
            task1 = dbutils.addTask(prj.name, "task1", interactive=False)
            task2 = dbutils.addTask(prj2.name, "task2", interactive=False)
            self.session.commit()

            renamedProjectPath = createProjectFile(
                    tmpDir,
                    name="prj",
                    uuid=prj2.uuid)

            class MyPullUi(PullUi):
                def getMergeStrategy(self, local, remote):
                    return PullUi.MERGE

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.modified = {renamedProjectPath}
                    return changes

            # Do the pull
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl=vcsImpl, pullUi=MyPullUi())

            # There should be only project, task1 and task2 should be associated
            # with it
            projects = list(self.session.query(Project).all())
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0].uuid, prj.uuid)
            self.assertEqual(projects[0].name, prj.name)

            taskDict = { x.uuid: x for x in self.session.query(Task).all()}
            self.assertEqual(len(taskDict), 2)
            self.assertEqual(taskDict[task1.uuid].title, task1.title)
            self.assertEqual(taskDict[task2.uuid].title, task2.title)
            self.assertEqual(taskDict[task1.uuid].project.uuid, prj.uuid)
            self.assertEqual(taskDict[task2.uuid].project.uuid, prj.uuid)

    def testRemoteRenamedProjectLikeLocalProject_rename(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            prj2 = dbutils.getOrCreateProject("prj2", interactive=False)
            task1 = dbutils.addTask(prj.name, "task1", interactive=False)
            task2 = dbutils.addTask(prj2.name, "task2", interactive=False)
            self.session.commit()

            renamedProjectPath = createProjectFile(
                    tmpDir,
                    name="prj",
                    uuid=prj2.uuid)

            class MyPullUi(PullUi):
                def resolveConflicts(self, vcsImpl):
                    return True

                def getMergeStrategy(self, local, remote):
                    return PullUi.RENAME

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.modified = {renamedProjectPath}
                    return changes

            # Do the pull
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl=vcsImpl, pullUi=MyPullUi())

            # prj2 should be renamed prj_1
            projectDict = { x.uuid: x for x in self.session.query(Project).all()}
            self.assertEqual(len(projectDict), 2)

            self.assertEqual(projectDict[prj.uuid].name, prj.name)
            self.assertEqual(projectDict[prj2.uuid].name, prj.name + "_1")
