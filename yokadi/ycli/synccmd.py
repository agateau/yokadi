import os
from cmd import Cmd

from yokadi.core import basepaths
from yokadi.sync import dump, pull
from yokadi.sync.conflictingobject import BothModifiedConflictingObject
from yokadi.sync.pullui import PullUi
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

    def do_s_dump(self, line):
        dump.dump(self.dumpDir)
        print('Database dumped in {}'.format(self.dumpDir))

    def do_s_pull(self, line):
        pull.pull(self.dumpDir, pullUi=TextPullUi())
