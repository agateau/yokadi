import json
import os
import unittest

from collections import namedtuple
from tempfile import TemporaryDirectory

from yokadi.core import db, dbutils
from yokadi.core.db import Task, Project
from yokadi.sync import PROJECTS_DIRNAME, TASKS_DIRNAME
from yokadi.sync import initDumpRepository, dump, pull, importSinceLastSync, importAll
from yokadi.sync.pullui import PullUi
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync.vcschanges import VcsChanges
from yokadi.sync.vcsconflict import VcsConflict


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

    def closeConflict(self, path, content):
        pass

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


def createTaskJson(uuid, projectUuid, title, **kwargs):
    dct = {
        "projectUuid": projectUuid,
        "uuid": uuid,
        "title": title,
        "creationDate": "2016-01-12T19:12:00",
        "keywords": {},
        "description": "",
    }
    dct.update(kwargs)
    return json.dumps(dct)


def createTaskFile(dirname, uuid, projectUuid, title, **kwargs):
    taskDir = os.path.join(dirname, TASKS_DIRNAME)
    if not os.path.exists(taskDir):
        os.mkdir(taskDir)
    filePath = os.path.join(taskDir, uuid + ".json")
    with open(filePath, "wt") as fp:
        fp.write(createTaskJson(uuid, projectUuid, title, **kwargs))
    return os.path.relpath(filePath, dirname)


BothModifiedConflictFixture = namedtuple("BothModifiedConflictFixture",
    ["modifiedTask", "vcsImpl"])


def createBothModifiedConflictFixture(testCase, session, tmpDir, localChanges, remoteChanges):
    prj = dbutils.getOrCreateProject("prj", interactive=False)

    modifiedTask = dbutils.addTask("prj", "Local title", interactive=False)
    modifiedTask.uuid = "1234-conflict"
    session.add(modifiedTask)

    modifiedTaskPath = os.path.join(TASKS_DIRNAME, modifiedTask.uuid + ".json")
    os.mkdir(os.path.join(tmpDir, TASKS_DIRNAME))

    class MyVcsImpl(StubVcsImpl):
        def __init__(self):
            self.abortMergeCallCount = 0
            self.commitAllCallCount = 0
            self.pullCalled = False
            self.conflicts = [VcsConflict(
                path=modifiedTaskPath,
                ancestor=createTaskJson(
                    uuid=modifiedTask.uuid,
                    projectUuid=prj.uuid,
                    title="Ancestor"
                ),
                local=createTaskJson(
                    uuid=modifiedTask.uuid,
                    projectUuid=prj.uuid,
                    **localChanges
                ),
                remote=createTaskJson(
                    uuid=modifiedTask.uuid,
                    projectUuid=prj.uuid,
                    **remoteChanges
                )
            )]

        def pull(self):
            self.pullCalled = True

        def getChangesSince(self, commitId):
            # This is called after the conflict has been resolved, so it
            # must return the task as modified
            changes = VcsChanges()
            changes.modified = {modifiedTaskPath}
            return changes

        def closeConflict(self, path, content):
            testCase.assertEqual(path, self.conflicts[0].path)
            fullPath = os.path.join(tmpDir, path)
            with open(fullPath, "wt") as fp:
                fp.write(content)
            self.conflicts = []

        def isWorkTreeClean(self):
            if not self.pullCalled:
                return True
            return not self.hasConflicts() and self.commitAllCallCount > 0

        def getConflicts(self):
            return self.conflicts

        def abortMerge(self):
            self.abortMergeCallCount += 1

        def commitAll(self, message=""):
            self.commitAllCallCount += 1

    return BothModifiedConflictFixture(
        modifiedTask=modifiedTask,
        vcsImpl=MyVcsImpl())


ModifiedDeletedConflictFixture = namedtuple("ModifiedDeletedConflictFixture",
    ["modLocallyTask", "modLocallyTaskPath", "modRemotelyTask", "modRemotelyTaskPath", "vcsImpl"])


def createModifiedDeletedConflictFixture(testCase, tmpDir):
    os.mkdir(os.path.join(tmpDir, TASKS_DIRNAME))

    prj = dbutils.getOrCreateProject("prj", interactive=False)

    # A task which has been modified locally but modRemotely remotely
    modLocallyTask = dbutils.addTask("prj", "Modified locally", interactive=False)
    modLocallyTask.uuid = "1234-modLocally"
    modLocallyTaskPath = os.path.join(TASKS_DIRNAME, modLocallyTask.uuid + ".json")

    # A task which has been modRemotely locally but modified remotely
    modRemotelyTask = Task() #dbutils.addTask("prj", "Removed", interactive=False)
    modRemotelyTask.uuid = "1234-modRemotely"
    modRemotelyTaskPath = os.path.join(TASKS_DIRNAME, modRemotelyTask.uuid + ".json")

    class MyVcsImpl(StubVcsImpl):
        def __init__(self):
            self.abortMergeCallCount = 0
            self.commitAllCallCount = 0
            self.pullCalled = False
            self.conflicts = [VcsConflict(
                path=modLocallyTaskPath,
                ancestor=createTaskJson(
                    uuid=modLocallyTask.uuid,
                    projectUuid=prj.uuid,
                    title="Ancestor"
                ),
                local=createTaskJson(
                    uuid=modLocallyTask.uuid,
                    projectUuid=prj.uuid,
                    title=modLocallyTask.title
                ),
                remote=None
            ),
            VcsConflict(
                path=modRemotelyTaskPath,
                ancestor=createTaskJson(
                    uuid=modRemotelyTask.uuid,
                    projectUuid=prj.uuid,
                    title="Ancestor"
                ),
                local=None,
                remote=createTaskJson(
                    uuid=modRemotelyTask.uuid,
                    projectUuid=prj.uuid,
                    title="Modified remotely"
                )
            )]

        def pull(self):
            self.pullCalled = True

        def getChangesSince(self, commitId):
            # This is called after the conflict has been resolved
            changes = VcsChanges()
            changes.modRemotely = {modRemotelyTaskPath}
            changes.added = {modLocallyTaskPath}
            return changes

        def closeConflict(self, path, content):
            testCase.assertTrue(path in (modLocallyTaskPath, modRemotelyTaskPath))
            if content is not None:
                fullPath = os.path.join(tmpDir, path)
                with open(fullPath, "wt") as fp:
                    fp.write(content)
            self.conflicts = []

        def isWorkTreeClean(self):
            if not self.pullCalled:
                return True
            return not self.hasConflicts() and self.commitAllCallCount > 0

        def getConflicts(self):
            return self.conflicts

        def abortMerge(self):
            self.abortMergeCallCount += 1

        def commitAll(self, message=""):
            self.commitAllCallCount += 1

    return ModifiedDeletedConflictFixture(
        modLocallyTask=modLocallyTask,
        modLocallyTaskPath=modLocallyTaskPath,
        modRemotelyTask=modRemotelyTask,
        modRemotelyTaskPath=modRemotelyTaskPath,
        vcsImpl=MyVcsImpl()
    )


class PullTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

    def testNothingToDo(self):
        with TemporaryDirectory() as tmpDir:
            vcsImpl = StubVcsImpl()
            pull(tmpDir, vcsImpl)
            importSinceLastSync(tmpDir, vcsImpl=vcsImpl)

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
            vcsImpl = MyVcsImpl()
            pull(tmpDir, vcsImpl=vcsImpl)
            importSinceLastSync(tmpDir, vcsImpl=vcsImpl)

            # Check changes
            modifiedTask2 = dbutils.getTask(self.session, id=modifiedTask.id)
            self.assertEqual(modifiedTask2.project.name, "prj2")
            self.assertEqual(modifiedTask2.title, "New task title")

            addedTask = self.session.query(Task).filter_by(uuid="1234-added").one()
            self.assertEqual(addedTask.project.name, "prj")
            self.assertEqual(addedTask.title, "Added")

            lst = self.session.query(Task).filter_by(id=removedTask.id)
            self.assertEqual(len(list(lst)), 0)

    def testConflictsAbortMerge(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)

            modifiedTask = dbutils.addTask("prj", "Local title", interactive=False)
            modifiedTask.uuid = "1234-conflict"
            self.session.add(modifiedTask)

            modifiedTaskPath = os.path.join(TASKS_DIRNAME, modifiedTask.uuid + ".json")

            class MyPullUi(PullUi):
                def resolveConflicts(self, conflictingObjects):
                    pass

            class MyVcsImpl(StubVcsImpl):
                def __init__(self):
                    self.abortMergeCallCount = 0
                    self.commitAllCallCount = 0
                    self.pullCalled = False

                def pull(self):
                    self.pullCalled = True

                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.added = {modifiedTaskPath}
                    return changes

                def isWorkTreeClean(self):
                    return not self.pullCalled

                def hasConflicts(self):
                    return self.pullCalled

                def getConflicts(self):
                    return [VcsConflict(
                        path=modifiedTaskPath,
                        ancestor=createTaskJson(
                            uuid=modifiedTask.uuid,
                            projectUuid=prj.uuid,
                            title="Ancestor"
                        ),
                        local=createTaskJson(
                            uuid=modifiedTask.uuid,
                            projectUuid=prj.uuid,
                            title="Local title"
                        ),
                        remote=createTaskJson(
                            uuid=modifiedTask.uuid,
                            projectUuid=prj.uuid,
                            title="Remote title"
                        )
                    )]

                def abortMerge(self):
                    self.abortMergeCallCount += 1

                def commitAll(self, message=""):
                    self.commitAllCallCount += 1

            # Do the pull
            vcsImpl = MyVcsImpl()
            pullUi = MyPullUi()
            ok = pull(tmpDir, vcsImpl=vcsImpl, pullUi=pullUi)

            # Check changes. Since there was a conflict there should be no
            # commit.
            self.assertFalse(ok)
            self.assertEqual(vcsImpl.abortMergeCallCount, 1)
            self.assertEqual(vcsImpl.commitAllCallCount, 0)

    def testBothModifiedConflictSolved(self):
        testCase = self
        with TemporaryDirectory() as tmpDir:
            fixture = createBothModifiedConflictFixture(self, self.session, tmpDir,
                localChanges=dict(
                    title="Local title",
                    description="Local description"
                ),
                remoteChanges=dict(
                    title="Remote title",
                    keywords={"remotekw": 1}
                ))

            class MyPullUi(PullUi):
                def resolveConflicts(self, conflictingObjects):
                    testCase.assertEqual(len(conflictingObjects), 1)
                    obj = conflictingObjects[0]
                    testCase.assertEqual(obj.conflictingKeys, {"title"})
                    obj.selectValue("title", "Merged title")

            # Do the pull
            pullUi = MyPullUi()
            pull(tmpDir, vcsImpl=fixture.vcsImpl, pullUi=pullUi)
            importSinceLastSync(tmpDir, vcsImpl=fixture.vcsImpl, pullUi=pullUi)

            # Check changes. Conflict has been solved, there should be a merge.
            self.assertEqual(fixture.vcsImpl.abortMergeCallCount, 0)
            self.assertEqual(fixture.vcsImpl.commitAllCallCount, 1)

            modifiedTask2 = dbutils.getTask(self.session, id=fixture.modifiedTask.id)
            self.assertEqual(modifiedTask2.title, "Merged title")
            # Description was only changed locally
            self.assertEqual(modifiedTask2.description, "Local description")
            # Keyword was only changed remotely
            self.assertEqual(modifiedTask2.getKeywordDict(), {"remotekw": 1})

    def testModifiedDeletedConflictSolved(self):
        testCase = self
        with TemporaryDirectory() as tmpDir:
            fixture = createModifiedDeletedConflictFixture(testCase,tmpDir)

            class MyPullUi(PullUi):
                def resolveConflicts(self, conflictingObjects):
                    testCase.assertEqual(len(conflictingObjects), 2)
                    dct = dict((x._path, x) for x in conflictingObjects)
                    dct[fixture.modLocallyTaskPath].selectLocal()
                    dct[fixture.modRemotelyTaskPath].selectRemote()

            # Do the pull
            pullUi = MyPullUi()
            pull(tmpDir, vcsImpl=fixture.vcsImpl, pullUi=pullUi)
            importSinceLastSync(tmpDir, vcsImpl=fixture.vcsImpl, pullUi=pullUi)

            # Check changes. Conflict has been solved, there should be a merge.
            self.assertEqual(fixture.vcsImpl.abortMergeCallCount, 0)
            self.assertEqual(fixture.vcsImpl.commitAllCallCount, 1)

            keptTask = dbutils.getTask(self.session, id=fixture.modLocallyTask.id)
            self.assertEqual(keptTask.title, fixture.modLocallyTask.title)

            self.assertFalse(dbutils.getTask(self.session, uuid=fixture.modRemotelyTask.uuid, _allowNone=True))

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
            importSinceLastSync(tmpDir, vcsImpl=vcsImpl)

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
            importSinceLastSync(tmpDir, vcsImpl=vcsImpl)

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
            importSinceLastSync(tmpDir, vcsImpl=vcsImpl)

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
            importSinceLastSync(tmpDir, vcsImpl=vcsImpl)

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
            pullUi = MyPullUi()
            pull(tmpDir, vcsImpl=vcsImpl, pullUi=pullUi)
            importSinceLastSync(tmpDir, vcsImpl=vcsImpl, pullUi=pullUi)

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
            pullUi = MyPullUi()
            pull(tmpDir, vcsImpl=vcsImpl, pullUi=pullUi)
            importSinceLastSync(tmpDir, vcsImpl=vcsImpl, pullUi=pullUi)

            # prj2 should be renamed prj_1
            projectDict = { x.uuid: x for x in self.session.query(Project).all()}
            self.assertEqual(len(projectDict), 2)

            self.assertEqual(projectDict[prj.uuid].name, prj.name)
            self.assertEqual(projectDict[prj2.uuid].name, prj.name + "_1")

    def testImportAll(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            prj2 = dbutils.getOrCreateProject("prj2", interactive=False)
            task1 = dbutils.addTask(prj.name, "task1", interactive=False)
            modifiedTask = dbutils.addTask(prj2.name, "task2", interactive=False)
            self.session.commit()

            dumpDir = os.path.join(tmpDir, "dump")
            initDumpRepository(dumpDir)
            dump(dumpDir)

            # Alter some files
            modifiedTaskPath = os.path.join(dumpDir, TASKS_DIRNAME, modifiedTask.uuid + ".json")
            createTaskFile(dumpDir, modifiedTask.uuid, modifiedTask.project.uuid,
                    title="modified", description="new description")
            vcsImpl = GitVcsImpl()
            vcsImpl.setDir(dumpDir)
            vcsImpl.commitAll()

            # Import all
            importAll(dumpDir)
