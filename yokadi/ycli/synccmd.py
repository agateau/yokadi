import os
from cmd import Cmd

from yokadi.core import basepaths
from yokadi.core.yokadioptionparser import YokadiOptionParser
from yokadi.sync.conflictingobject import BothModifiedConflictingObject
from yokadi.sync.pullui import PullUi
from yokadi.sync.vcsimplerrors import VcsImplError, NotFastForwardError
from yokadi.sync.syncmanager import SyncManager
from yokadi.ycli import tui


class TextPullUi(PullUi):
    def resolveConflicts(self, conflictingObjects):
        count = len(conflictingObjects)
        if count > 1:
            print("{} conflicts to resolve".format(count))
        else:
            print("One conflict to resolve")
        for obj in conflictingObjects:
            if isinstance(obj, BothModifiedConflictingObject):
                self.resolveBothModifiedObject(obj)
            else:
                self.resolveModifiedDeletedObject(obj)
            assert obj.isResolved()

    def getMergeStrategy(self, localProjectDict, remoteProjectDict):
        name = localProjectDict["name"]
        print("Remote and local databases contain a project named '{}'.".format(name))
        answers = (
            (1, "Merge them"),
            (2, "Rename the local project"),
            (3, "Cancel")
        )
        answer = tui.selectFromList("Select next action", answers, default=None)
        if answer == 1:
            return PullUi.MERGE
        elif answer == 2:
            return PullUi.RESET
        else:
            return PullUi.CANCEL

    def resolveBothModifiedObject(self, obj):
        for key in set(obj.conflictingKeys):
            oldValue = obj.ancestor[key]
            print("\n# Conflict on \"{}\" key. Old value was \"{}\".".format(key, oldValue))
            answers = (
                (1, "Local value: \"{}\"".format(obj.local[key])),
                (2, "Remote value: \"{}\"".format(obj.remote[key]))
            )
            answer = tui.selectFromList("Which version do you want to keep".format(key), answers, default=None)
            if answer == 1:
                value = obj.local[key]
            else:
                value = obj.remote[key]
            obj.selectValue(key, value)

    def resolveModifiedDeletedObject(self, obj):
        print()
        if obj.remote is None:
            print("This object has been modified locally and deleted remotely")
            modified = obj.local
        else:
            print("This object has been modified remotely and deleted locally")
            modified = obj.remote
        for key, value in obj.ancestor.items():
            modifiedValue = modified[key]
            if value == modifiedValue:
                print("- {}: {}".format(key, value))
            else:
                print("- {}: {} => {}".format(key, value, modifiedValue))
        answers = (
            (1, "Local"),
            (2, "Remote")
        )
        answer = tui.selectFromList("Which version do you want to keep", answers, default=None)
        if answer == 1:
            obj.selectLocal()
        else:
            obj.selectRemote()


class SyncCmd(Cmd):
    def __init__(self):
        self.dumpDir = os.path.join(basepaths.getCacheDir(), 'db')
        self.syncManager = SyncManager(self.dumpDir)

    def do_s_sync(self, line):
        pullUi = TextPullUi()

        print("Dumping database")
        self.syncManager.dump()

        while True:
            print("Pulling remote changes")
            self.syncManager.pull(pullUi=pullUi)
            if self.syncManager.hasChangesToImport():
                print("Importing changes")
                self.syncManager.importSinceLastSync(pullUi=pullUi)
            else:
                print("No remote changes")

            if not self.syncManager.hasChangesToPush():
                return
            print("Pushing local changes")
            try:
                self.syncManager.push()
                return
            except NotFastForwardError:
                print("Remote has other changes, need to pull again")
            except VcsImplError as exc:
                print("Failed to push: {}".format(exc))
                return

    def do_s_init(self, line):
        self.syncManager.initDumpRepository()
        self.syncManager.dump()
        print('Synchronization initialized, repository is in {}'.format(self.dumpDir))

    def do_s_dump(self, line):
        self.syncManager.dump()
        print('Database dumped in {}'.format(self.dumpDir))

    def do_s_pull(self, line):
        parser = self.parser_s_pull()
        args = parser.parse_args(line)
        pullUi = TextPullUi()
        self.syncManager.pull(pullUi=pullUi)
        if args.all:
            self.syncManager.importAll(pullUi=pullUi)
        else:
            self.syncManager.importSinceLastSync(pullUi=pullUi)

    def parser_s_pull(self):
        parser = YokadiOptionParser()
        parser.usage = "s_pull [options]"
        parser.description = "Pull changes from a remote repository"
        parser.add_argument("--all", dest="all", default=False, action="store_true",
                            help="Import all changes, regardless of the current synchronization status")
        return parser

    def do_s_push(self, line):
        try:
            self.syncManager.push()
        except NotFastForwardError:
            print("Remote has other changes, you need to run s_pull")
        except VcsImplError as exc:
            print("Failed to push: {}".format(exc))
