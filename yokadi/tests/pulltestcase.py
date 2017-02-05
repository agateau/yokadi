"""
Test cases for pull functions

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os

from collections import namedtuple
from tempfile import TemporaryDirectory

from yokadi.core import db, dbutils
from yokadi.core.db import Task, Project
from yokadi.sync import ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME
from yokadi.sync.dump import createVersionFile, jsonDump, jsonDumps
from yokadi.sync.pull import ChangeHandler
from yokadi.sync.syncmanager import SyncManager
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync.vcschanges import VcsChanges
from yokadi.sync.vcsconflict import VcsConflict
from yokadi.sync.vcsimpl import VcsImpl
from yokadi.sync.vcsimplerrors import VcsImplError
from yokadi.sync.syncerrors import MergeError
from yokadi.tests.yokaditestcase import YokadiTestCase
from yokadi.tests.stubpullui import StubPullUi


class StubVcsImpl(VcsImpl):
    def __init__(self, srcDir):
        self._tags = set()
        self._srcDir = srcDir

    @property
    def srcDir(self):
        return self._srcDir

    def isValidVcsDir(self):
        return True

    def init(self):
        pass

    def fetch(self):
        pass

    def merge(self):
        pass

    def hasConflicts(self):
        return bool(self.getConflicts())

    def getConflicts(self):
        return []

    def isWorkTreeClean(self):
        return True

    def closeConflict(self, path, content):
        pass

    def commitAll(self, message=None):
        pass

    def getChangesSince(self, commitId):
        return VcsChanges()

    def getWorkTreeChanges(self):
        return VcsChanges()

    def updateBranch(self, branch, commitId):
        pass

    def hasTag(self, tag):
        return tag in self._tags

    def createTag(self, tag):
        if tag in self._tags:
            raise VcsImplError("tag {} already exists".format(tag))
        self._tags.add(tag)

    def deleteTag(self, tag):
        try:
            self._tags.remove(tag)
        except KeyError:
            raise VcsImplError("tag {} does not exist".format(tag))


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
        jsonDump(dct, fp)
    return os.path.relpath(filePath, dirname)


def createTaskJson(uuid, projectUuid, title, **kwargs):
    dct = {
        "projectUuid": projectUuid,
        "uuid": uuid,
        "title": title,
        "creationDate": "2016-01-12T19:12:00",
        "keywords": {},
        "description": "",
        "recurrence": {},
        "status": "new",
        "urgency": 0,
    }
    dct.update(kwargs)
    return jsonDumps(dct).encode("utf-8")


def createTaskFile(dirname, uuid, projectUuid, title, **kwargs):
    taskDir = os.path.join(dirname, TASKS_DIRNAME)
    if not os.path.exists(taskDir):
        os.mkdir(taskDir)
    filePath = os.path.join(taskDir, uuid + ".json")
    with open(filePath, "wb") as fp:
        fp.write(createTaskJson(uuid, projectUuid, title, **kwargs))
    return os.path.relpath(filePath, dirname)


def createAliasFile(dirname, uuid, name, command):
    aliasesDir = os.path.join(dirname, ALIASES_DIRNAME)
    if not os.path.exists(aliasesDir):
        os.mkdir(aliasesDir)
    dct = {
        "uuid": uuid,
        "name": name,
        "command": command,
    }
    filePath = os.path.join(aliasesDir, uuid + ".json")
    with open(filePath, "wt") as fp:
        jsonDump(dct, fp)
    return os.path.relpath(filePath, dirname)


BothModifiedConflictFixture = namedtuple("BothModifiedConflictFixture",
    ["modifiedTask", "vcsImpl"])


def createBothModifiedConflictFixture(testCase, session, tmpDir, localChanges, remoteChanges):
    createVersionFile(tmpDir)
    os.mkdir(os.path.join(tmpDir, TASKS_DIRNAME))
    os.mkdir(os.path.join(tmpDir, PROJECTS_DIRNAME))
    os.mkdir(os.path.join(tmpDir, ALIASES_DIRNAME))

    prj = dbutils.getOrCreateProject("prj", interactive=False)

    modifiedTask = dbutils.addTask("prj", "Local title", interactive=False)
    modifiedTask.uuid = "1234-conflict"
    session.add(modifiedTask)

    modifiedTaskPath = os.path.join(TASKS_DIRNAME, modifiedTask.uuid + ".json")

    class MyVcsImpl(StubVcsImpl):
        def __init__(self, srcDir):
            StubVcsImpl.__init__(self, srcDir)
            self.commitAllCallCount = 0
            self.mergeCalled = False
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

        def merge(self):
            self.mergeCalled = True

        def getChangesSince(self, commitId):
            # This is called after the conflict has been resolved, so it
            # must return the task as modified
            changes = VcsChanges()
            changes.modified = {modifiedTaskPath}
            return changes

        def closeConflict(self, path, content):
            testCase.assertEqual(path, self.conflicts[0].path)
            fullPath = os.path.join(tmpDir, path)
            with open(fullPath, "wb") as fp:
                fp.write(content)
            self.conflicts = []

        def isWorkTreeClean(self):
            if not self.mergeCalled:
                return True
            return not self.hasConflicts() and self.commitAllCallCount > 0

        def getConflicts(self):
            return self.conflicts

        def commitAll(self, message=""):
            self.commitAllCallCount += 1

    return BothModifiedConflictFixture(
        modifiedTask=modifiedTask,
        vcsImpl=MyVcsImpl(tmpDir))


ModifiedDeletedConflictFixture = namedtuple("ModifiedDeletedConflictFixture",
    ["modLocallyTask", "modLocallyTaskPath", "modRemotelyTask", "modRemotelyTaskPath", "vcsImpl"])


def createModifiedDeletedConflictFixture(testCase, tmpDir):
    createVersionFile(tmpDir)
    os.mkdir(os.path.join(tmpDir, TASKS_DIRNAME))
    os.mkdir(os.path.join(tmpDir, PROJECTS_DIRNAME))
    os.mkdir(os.path.join(tmpDir, ALIASES_DIRNAME))

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
        def __init__(self, srcDir):
            StubVcsImpl.__init__(self, srcDir)
            self.commitAllCallCount = 0
            self.mergeCalled = False
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

        def merge(self):
            self.mergeCalled = True

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
                with open(fullPath, "wb") as fp:
                    fp.write(content)
            self.conflicts = []

        def isWorkTreeClean(self):
            if not self.mergeCalled:
                return True
            return not self.hasConflicts() and self.commitAllCallCount > 0

        def getConflicts(self):
            return self.conflicts

        def commitAll(self, message=""):
            self.commitAllCallCount += 1

    return ModifiedDeletedConflictFixture(
        modLocallyTask=modLocallyTask,
        modLocallyTaskPath=modLocallyTaskPath,
        modRemotelyTask=modRemotelyTask,
        modRemotelyTaskPath=modRemotelyTaskPath,
        vcsImpl=MyVcsImpl(tmpDir)
    )


class PullTestCase(YokadiTestCase):
    def setUp(self):
        YokadiTestCase.setUp(self)
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

    def testNothingToDo(self):
        with TemporaryDirectory() as tmpDir:
            createVersionFile(tmpDir)
            syncManager = SyncManager(session=self.session, vcsImpl=StubVcsImpl(tmpDir))
            syncManager.pull(pullUi=StubPullUi())

    def testOnlyImportOurFiles(self):
        class FooChangeHandler(ChangeHandler):
            domain = "foo"
        self.assertTrue(FooChangeHandler._shouldHandleFilePath("foo/123.json"))
        self.assertFalse(FooChangeHandler._shouldHandleFilePath("bar/123.json"))
        self.assertFalse(FooChangeHandler._shouldHandleFilePath("foo/123.garbage"))

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
            createVersionFile(tmpDir)
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
            syncManager = SyncManager(session=self.session, vcsImpl=MyVcsImpl(tmpDir))
            syncManager.pull(pullUi=StubPullUi())

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

            class MyVcsImpl(StubVcsImpl):
                def __init__(self, srcDir):
                    StubVcsImpl.__init__(self, srcDir)
                    self.commitAllCallCount = 0
                    self.mergeCalled = False

                def merge(self):
                    self.mergeCalled = True

                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.added = {modifiedTaskPath}
                    return changes

                def isWorkTreeClean(self):
                    return not self.mergeCalled

                def hasConflicts(self):
                    return self.mergeCalled

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

                def commitAll(self, message=""):
                    self.commitAllCallCount += 1

            # Do the pull
            vcsImpl = MyVcsImpl(tmpDir)
            pullUi = StubPullUi()
            syncManager = SyncManager(session=self.session, vcsImpl=vcsImpl)
            self.assertRaises(MergeError, syncManager.pull, pullUi=pullUi)

            # Check changes. Since there was a conflict there should be no
            # commit.
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

            class MyPullUi(StubPullUi):
                def resolveConflicts(self, conflictingObjects):
                    testCase.assertEqual(len(conflictingObjects), 1)
                    obj = conflictingObjects[0]
                    testCase.assertEqual(obj.conflictingKeys, {"title"})
                    obj.selectValue("title", "Merged title")

            # Do the pull
            pullUi = MyPullUi()
            syncManager = SyncManager(session=self.session, vcsImpl=fixture.vcsImpl)
            syncManager.pull(pullUi=pullUi)

            # Check changes. Conflict has been solved, there should be a merge.
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

            class MyPullUi(StubPullUi):
                def resolveConflicts(self, conflictingObjects):
                    testCase.assertEqual(len(conflictingObjects), 2)
                    dct = dict((x._path, x) for x in conflictingObjects)
                    dct[fixture.modLocallyTaskPath].selectLocal()
                    dct[fixture.modRemotelyTaskPath].selectRemote()

            # Do the pull
            syncManager = SyncManager(session=self.session, vcsImpl=fixture.vcsImpl)
            pullUi = MyPullUi()
            syncManager.pull(pullUi=pullUi)

            # Check changes. Conflict has been solved, there should be a merge.
            self.assertEqual(fixture.vcsImpl.commitAllCallCount, 1)

            keptTask = dbutils.getTask(self.session, id=fixture.modLocallyTask.id)
            self.assertEqual(keptTask.title, fixture.modLocallyTask.title)

            self.assertFalse(dbutils.getTask(self.session, uuid=fixture.modRemotelyTask.uuid, _allowNone=True))

    def testProjectUpdated(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            self.session.commit()

            createVersionFile(tmpDir)
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
            pullUi = StubPullUi()
            syncManager = SyncManager(session=self.session, vcsImpl=MyVcsImpl(tmpDir))
            syncManager.pull(pullUi=pullUi)

            # Check changes
            prj2 = self.session.query(Project).filter_by(id=prj.id).one()
            self.assertEqual(prj2.name, "prj2")

    def testProjectRemoved(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            task = dbutils.addTask(prj.name, "title", interactive=False)
            self.session.commit()

            createVersionFile(tmpDir)
            removedProjectPath = os.path.join(PROJECTS_DIRNAME, prj.uuid + ".json")
            removedTaskPath = os.path.join(TASKS_DIRNAME, task.uuid + ".json")

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.removed = {removedProjectPath, removedTaskPath}
                    return changes

            # Do the pull
            pullUi = StubPullUi()
            syncManager = SyncManager(session=self.session, vcsImpl=MyVcsImpl(tmpDir))
            syncManager.pull(pullUi=pullUi)

            # DB should be empty
            projects = self.session.query(Project).all()
            self.assertEqual(len(list(projects)), 0)
            tasks = self.session.query(Task).all()
            self.assertEqual(len(list(tasks)), 0)

    def testRemoteCreateSameProject(self):
        with TemporaryDirectory() as tmpDir:
            REMOTE_PROJECT_UUID = "r-5678-prj2"
            pullUi = StubPullUi()

            # Create an empty remote repo
            remoteDir = os.path.join(tmpDir, "remote")
            remoteSyncManager = SyncManager(vcsImpl=GitVcsImpl(remoteDir))
            remoteSyncManager.initDumpRepository()

            # Clone the remote repo
            localDir = os.path.join(tmpDir, "local")
            syncManager = SyncManager(session=self.session, vcsImpl=GitVcsImpl(localDir))
            syncManager.vcsImpl.clone(remoteDir)
            syncManager.pull(pullUi=pullUi)

            # Create prj in remote repo
            createProjectFile(
                    remoteDir,
                    uuid=REMOTE_PROJECT_UUID,
                    name="prj")
            createTaskFile(
                    remoteDir,
                    title="r-task",
                    projectUuid=REMOTE_PROJECT_UUID,
                    uuid="r-1234-task")
            remoteSyncManager.vcsImpl.commitAll()

            # Create prj in local repo
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            task = dbutils.addTask(prj.name, "l-task", interactive=False)
            self.session.commit()
            prjUuid = prj.uuid
            syncManager.dump()

            # Do the pull, conflict should be automatically solved
            syncManager.pull(pullUi=pullUi)

            # Local project should be renamed prj_1
            projects = list(self.session.query(Project).all())
            self.assertCountEqual(
                    (x.uuid for x in projects),
                    (prjUuid, REMOTE_PROJECT_UUID))
            self.assertCountEqual(
                    (x.name for x in projects),
                    ("prj", "prj_1"))

            tasks = list(self.session.query(Task).all())
            self.assertCountEqual(
                    (x.uuid for x in tasks),
                    (task.uuid, "r-1234-task"))
            self.assertCountEqual(
                    (x.title for x in tasks),
                    ("l-task", "r-task"))

    def testRemoteRenamedProject(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            task1 = dbutils.addTask(prj.name, "task1", interactive=False)
            self.session.commit()

            createVersionFile(tmpDir)
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
            syncManager = SyncManager(session=self.session, vcsImpl=MyVcsImpl(tmpDir))
            syncManager.pull(pullUi=StubPullUi())

            # The project should have a new name, task1 should still be there
            projects = list(self.session.query(Project).all())
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0].uuid, prj.uuid)
            self.assertEqual(projects[0].name, "prj2")

            tasks = list(self.session.query(Task).all())
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].project.uuid, prj.uuid)
            self.assertEqual(tasks[0].title, task1.title)

    def testRemoteRenamedProjectLikeLocalProject(self):
        with TemporaryDirectory() as tmpDir:
            # Create a remote repo with project "remote" and a task task1
            remoteDir = os.path.join(tmpDir, "remote")
            remoteSyncManager = SyncManager(vcsImpl=GitVcsImpl(remoteDir))
            remoteSyncManager.initDumpRepository()

            createProjectFile(remoteDir, uuid="u-rprj", name="remote")
            createTaskFile(remoteDir, uuid="u-rtask", projectUuid="u-rprj", title="rtask")
            remoteSyncManager.vcsImpl.commitAll()

            # Clone the remote repo
            localDir = os.path.join(tmpDir, "local")
            syncManager = SyncManager(session=self.session, vcsImpl=GitVcsImpl(localDir))
            syncManager.vcsImpl.clone(remoteDir)
            pullUi = StubPullUi()
            syncManager.pull(pullUi=pullUi)
            syncManager.importAll(pullUi=pullUi)

            # Create "local" project in local repo, with task ltask
            localPrj = Project(uuid="u-lprj", name="local")
            self.session.add(localPrj)
            dbutils.addTask(localPrj.name, "ltask", interactive=False)
            self.session.commit()
            syncManager.dump()

            # Rename "remote" to "local" in remote repo
            createProjectFile(remoteDir, uuid="u-rprj", name=localPrj.name)
            remoteSyncManager.vcsImpl.commitAll()

            # Do the pull, conflict should be automatically solved
            pullUi = StubPullUi()
            syncManager.pull(pullUi=pullUi)

            # Check changes
            self.assertTrue(syncManager.vcsImpl.isWorkTreeClean())
            self.assertEqual(pullUi.renames, [(PROJECTS_DIRNAME, "local", "local_1")])

            remoteProject = dbutils.getProject(self.session, uuid="u-rprj")
            localProject = dbutils.getProject(self.session, uuid="u-lprj")

            names = {localProject.name, remoteProject.name}
            self.assertEqual(names, {"local", "local_1"})

            task = dbutils.getTask(self.session, project=remoteProject)
            self.assertEqual(task.title, "rtask")

            task = dbutils.getTask(self.session, project=localProject)
            self.assertEqual(task.title, "ltask")

    def testRemoteSwappedProjectNames(self):
        with TemporaryDirectory() as tmpDir:
            # Create a remote repo with project p1 (task task1) and p2 (task
            # task2)
            remoteDir = os.path.join(tmpDir, "remote")
            remoteSyncManager = SyncManager(vcsImpl=GitVcsImpl(remoteDir))
            remoteSyncManager.initDumpRepository()

            createProjectFile(remoteDir, uuid="u-prj1", name="p1")
            createProjectFile(remoteDir, uuid="u-prj2", name="p2")
            createTaskFile(remoteDir, uuid="u-task1", projectUuid="u-prj1", title="task1")
            createTaskFile(remoteDir, uuid="u-task2", projectUuid="u-prj2", title="task2")
            remoteSyncManager.vcsImpl.commitAll()

            # Clone the remote repo
            localDir = os.path.join(tmpDir, "local")
            syncManager = SyncManager(session=self.session, vcsImpl=GitVcsImpl(localDir))
            syncManager.vcsImpl.clone(remoteDir)
            pullUi = StubPullUi()
            syncManager.pull(pullUi=pullUi)
            syncManager.importAll(pullUi=pullUi)

            # Swap project names in remote repo
            createProjectFile(remoteDir, uuid="u-prj1", name="p2")
            createProjectFile(remoteDir, uuid="u-prj2", name="p1")
            remoteSyncManager.vcsImpl.commitAll()

            # Do the pull, conflict should be automatically solved
            syncManager.pull(pullUi=pullUi)

            # Check changes, now p1 should have a task task2 and p2 a task task1
            p1 = dbutils.getProject(self.session, uuid="u-prj2")
            self.assertEqual(p1.name, "p1")

            p2 = dbutils.getProject(self.session, uuid="u-prj1")
            self.assertEqual(p2.name, "p2")

            task = dbutils.getTask(self.session, project=p1)
            self.assertEqual(task.title, "task2")

            task = dbutils.getTask(self.session, project=p2)
            self.assertEqual(task.title, "task1")

    def testImportAll(self):
        with TemporaryDirectory() as tmpDir:
            prj = dbutils.getOrCreateProject("prj", interactive=False)
            prj2 = dbutils.getOrCreateProject("prj2", interactive=False)
            task1 = dbutils.addTask(prj.name, "task1", interactive=False)
            modifiedTask = dbutils.addTask(prj2.name, "task2", interactive=False)
            self.session.commit()

            dumpDir = os.path.join(tmpDir, "dump")
            vcsImpl = GitVcsImpl(dumpDir)
            syncManager = SyncManager(session=self.session, vcsImpl=vcsImpl)
            syncManager.initDumpRepository()
            syncManager.dump()

            # Alter some files
            modifiedTaskPath = os.path.join(dumpDir, TASKS_DIRNAME, modifiedTask.uuid + ".json")
            createTaskFile(dumpDir, modifiedTask.uuid, modifiedTask.project.uuid,
                    title="modified", description="new description")
            vcsImpl.commitAll()

            # Import all
            syncManager.importAll(pullUi=StubPullUi())

            modifiedTask2 = dbutils.getTask(self.session, uuid=modifiedTask.uuid)
            self.assertEqual(modifiedTask2.title, "modified")
            self.assertEqual(modifiedTask2.description, "new description")

    def testImportAlias(self):
        with TemporaryDirectory() as tmpDir:
            createVersionFile(tmpDir)
            aliasPath = createAliasFile(tmpDir, uuid="123", name="a", command="t_add")

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.added = {aliasPath}
                    return changes

            # Do the pull
            syncManager = SyncManager(session=self.session, vcsImpl=MyVcsImpl(tmpDir))
            syncManager.pull(pullUi=StubPullUi())

            # Check changes
            dct = db.Alias.getAsDict(self.session)
            self.assertEqual(dct, dict(a="t_add"))

    def testImportAlias_removed(self):
        db.Alias.add(self.session, "a", "t_add")
        a2 = db.Alias.add(self.session, "a2", "t_add2")
        self.session.flush()
        with TemporaryDirectory() as tmpDir:
            createVersionFile(tmpDir)
            removedAliasPath = os.path.join(ALIASES_DIRNAME, a2.uuid + ".json")

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.removed = {removedAliasPath}
                    return changes

            # Do the pull
            syncManager = SyncManager(session=self.session, vcsImpl=MyVcsImpl(tmpDir))
            syncManager.pull(pullUi=StubPullUi())

            # Check changes
            dct = db.Alias.getAsDict(self.session)
            self.assertEqual(dct, dict(a="t_add"))

    def testImportAlias_sameNameSameCommand(self):
        with TemporaryDirectory() as tmpDir:
            pullUi = StubPullUi()
            # Create an empty remote repo
            remoteDir = os.path.join(tmpDir, "remote")
            remoteSyncManager = SyncManager(vcsImpl=GitVcsImpl(remoteDir))
            remoteSyncManager.initDumpRepository()

            # Clone the remote repo
            localDir = os.path.join(tmpDir, "local")
            syncManager = SyncManager(session=self.session, vcsImpl=GitVcsImpl(localDir))
            syncManager.vcsImpl.clone(remoteDir)
            syncManager.pull(pullUi=pullUi)

            # Add an alias a => t_add to the remote repo
            aliasPath = createAliasFile(remoteDir, uuid="123", name="a", command="t_add")
            remoteSyncManager.vcsImpl.commitAll()

            # Init the local db with the same alias
            alias = db.Alias.add(self.session, "a", "t_add")
            self.session.commit()
            syncManager.dump()

            # Do the pull, conflict should be automatically solved
            syncManager.pull(pullUi=pullUi)

            # Check changes
            self.assertTrue(syncManager.vcsImpl.isWorkTreeClean())
            dct = db.Alias.getAsDict(self.session)
            self.assertEqual(dct, dict(a="t_add"))

    def testImportAlias_sameNameDifferentCommand(self):
        with TemporaryDirectory() as tmpDir:
            # Create an empty remote repo
            remoteDir = os.path.join(tmpDir, "remote")
            remoteSyncManager = SyncManager(vcsImpl=GitVcsImpl(remoteDir))
            remoteSyncManager.initDumpRepository()

            # Clone the remote repo
            localDir = os.path.join(tmpDir, "local")
            syncManager = SyncManager(session=self.session, vcsImpl=GitVcsImpl(localDir))
            syncManager.vcsImpl.clone(remoteDir)
            syncManager.pull(pullUi=StubPullUi())

            # Add an alias a => t_add to the remote repo
            aliasPath = createAliasFile(remoteDir, uuid="123", name="a", command="t_add")
            remoteSyncManager.vcsImpl.commitAll()

            # Init the local db with a different alias
            alias = db.Alias.add(self.session, "a", "t_add -d")
            self.session.commit()
            syncManager.dump()

            # Do the pull, conflict should be automatically solved
            pullUi = StubPullUi()
            syncManager.pull(pullUi=pullUi)

            # Check changes
            self.assertTrue(syncManager.vcsImpl.isWorkTreeClean())
            self.assertEqual(pullUi.renames, [(ALIASES_DIRNAME, "a", "a_1")])
            dct = db.Alias.getAsDict(self.session)
            self.assertEqual(dct, {"a_1": "t_add -d", "a": "t_add"})

    def testImportAlias_swapNames(self):
        with TemporaryDirectory() as tmpDir:
            alias1 = db.Alias.add(self.session, "a1", "a_one")
            alias2 = db.Alias.add(self.session, "a2", "a_two")
            self.session.flush()

            createVersionFile(tmpDir)
            alias1Path = createAliasFile(tmpDir, uuid=alias1.uuid, name=alias2.name, command=alias1.command)
            alias2Path = createAliasFile(tmpDir, uuid=alias2.uuid, name=alias1.name, command=alias2.command)

            class MyVcsImpl(StubVcsImpl):
                def getChangesSince(self, commitId):
                    changes = VcsChanges()
                    changes.modified = {alias1Path, alias2Path}
                    return changes

            # Do the pull
            syncManager = SyncManager(session=self.session, vcsImpl=MyVcsImpl(tmpDir))
            syncManager.pull(pullUi=StubPullUi())

            # Check changes
            dct = db.Alias.getAsDict(self.session)
            self.assertEqual(dct, dict(a1="a_two", a2="a_one"))
