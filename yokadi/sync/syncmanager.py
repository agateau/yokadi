"""
SyncManager
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import json
import os

from yokadi.core import db
from yokadi.sync import DB_SYNC_BRANCH, ALIASES_DIRNAME, PROJECTS_DIRNAME, \
        TASKS_DIRNAME
from yokadi.sync.gitvcsimpl import GitVcsImpl
from yokadi.sync.dump import clearDump, dump, createVersionFile, commitChanges

from yokadi.sync.dbreplicator import DbReplicator
from yokadi.sync.pull import pull, importSinceLastSync, importAll, findConflicts


class SyncManager(object):
    def __init__(self, dumpDir, *, session=None, vcsImpl=None):
        if vcsImpl is None:
            vcsImpl = GitVcsImpl()
        self.vcsImpl = vcsImpl
        self.dumpDir = dumpDir
        self.vcsImpl.setDir(dumpDir)

        self._pathsToDelete = set()
        self._dictsToWrite = {}

        if session:
            self._dbReplicator = DbReplicator(dumpDir, session)
            self.session = session

    def initDumpRepository(self):
        assert not os.path.exists(self.dumpDir), "Dump dir {} should not already exist".format(self.dumpDir)
        os.makedirs(self.dumpDir)
        self.vcsImpl.init()
        createVersionFile(self.dumpDir)
        for dirname in ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME:
            path = os.path.join(self.dumpDir, dirname)
            os.mkdir(path)
        self.commitChanges("Created")

    def clearDump(self):
        clearDump(self.dumpDir)

    def dump(self):
        dump(self.dumpDir, vcsImpl=self.vcsImpl)

    def commitChanges(self, message):
        commitChanges(self.dumpDir, message, vcsImpl=self.vcsImpl)

    def pull(self, pullUi):
        pull(self.dumpDir, vcsImpl=self.vcsImpl, pullUi=pullUi)

    def importSinceLastSync(self, pullUi):
        importSinceLastSync(self.dumpDir, vcsImpl=self.vcsImpl, pullUi=pullUi)

    def importAll(self, pullUi):
        importAll(self.dumpDir, vcsImpl=self.vcsImpl, pullUi=pullUi)

    def push(self):
        self.vcsImpl.push()

    def checkDumpIntegrity(self):
        self._checkItems(PROJECTS_DIRNAME, db.Project)
        self._checkItems(TASKS_DIRNAME, db.Task)
        self._checkItems(ALIASES_DIRNAME, db.Alias)
        self._checkUnicity(PROJECTS_DIRNAME)
        self._checkUnicity(ALIASES_DIRNAME)
        self._checkTaskProjects()

    def _checkItems(self, dirname, table):
        print("# Checking all {} are there".format(dirname))
        objectDir = os.path.join(self.dumpDir, dirname)
        dumpUuids = set()
        for name in os.listdir(objectDir):
            if not name.endswith(".json"):
                continue
            objectPath = os.path.join(objectDir, name)
            with open(objectPath) as fp:
                dct = json.load(fp)
            dumpUuids.add(dct["uuid"])

        query = self.session.query(table).all()
        dbUuids = set(x.uuid for x in query)

        if dbUuids != dumpUuids:
            missing = dumpUuids - dbUuids
            if missing:
                missing = '\n'.join(missing)
                print("## Missing DB items:\n{}\n".format(missing))
            missing = dbUuids - dumpUuids
            if missing:
                missing = '\n'.join(missing)
                print("## Missing dump items:\n{}\n".format(missing))

    def _checkUnicity(self, dirname):
        print("# Checking {} unicity".format(dirname))
        jsonDirPath = os.path.join(self.dumpDir, dirname)
        conflicts = findConflicts(jsonDirPath, "name")
        for name, conflictList in conflicts.items():
            print("## {} exists {} times".format(name, len(conflictList)))
            for conflict in conflictList:
                path = os.path.join(jsonDirPath, conflictList["uuid"] + ".json")
                print(path)

    def _checkTaskProjects(self):
        print("# Checking all tasks have an existing project")
        projectDir = os.path.join(self.dumpDir, PROJECTS_DIRNAME)
        taskDir = os.path.join(self.dumpDir, TASKS_DIRNAME)
        projectUuids = {os.path.splitext(x)[0] for x in os.listdir(projectDir)}

        first = True
        for taskName in os.listdir(taskDir):
            taskPath = os.path.join(taskDir, taskName)
            try:
                with open(taskPath) as fp:
                    dct = json.load(fp)
                if dct["projectUuid"] not in projectUuids:
                    if first:
                        print("These tasks point to a non existing project")
                        first = False
                    print(taskPath)
            except Exception as exc:
                raise Exception("Error in {}".format(taskPath)) from exc

    def hasChangesToCommit(self):
        return not self.vcsImpl.isWorkTreeClean()

    def hasChangesToImport(self):
        changes = self.vcsImpl.getChangesSince(DB_SYNC_BRANCH)
        return changes.hasChanges()

    def hasChangesToPush(self):
        changes = self.vcsImpl.getChangesSince("origin/master")
        return changes.hasChanges()
