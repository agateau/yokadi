#!/usr/bin/env python3
import os
import json
import unittest

from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.sync import ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME
from yokadi.sync.pullui import PullUi
from yokadi.sync.syncmanager import SyncManager


def getTaskPath(dumpDir, task):
    return os.path.join(dumpDir, TASKS_DIRNAME, task.uuid + ".json")


def getProjectPath(dumpDir, project):
    return os.path.join(dumpDir, PROJECTS_DIRNAME, project.uuid + ".json")


def getAliasPath(dumpDir, alias):
    return os.path.join(dumpDir, ALIASES_DIRNAME, alias.uuid + ".json")


class DumpTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        db.setDefaultConfig()
        self.session = db.getSession()

    def testDump(self):
        t1 = dbutils.addTask("prj1", "Foo", keywordDict=dict(kw1=1, kw2=None), interactive=False)
        t2 = dbutils.addTask("prj1", "Bar", keywordDict=dict(kw1=2), interactive=False)
        t3 = dbutils.addTask("prj2", "Baz", interactive=False)
        t3.description = "Hello"

        p1 = t1.project
        p2 = t3.project

        a1 = db.Alias.add(self.session, "a", "t_add")
        a2 = db.Alias.add(self.session, "ls", "t_list")

        with TemporaryDirectory() as tmpDir:
            dumpDir = os.path.join(tmpDir, "dump")
            syncManager = SyncManager(self.session, dumpDir)
            syncManager.initDumpRepository()
            syncManager.dump()

            for project in p1, p2:
                projectFilePath = getProjectPath(dumpDir, project)
                self.assertTrue(os.path.exists(projectFilePath))
                with open(projectFilePath) as f:
                    dct = json.load(f)
                    self.assertEqual(project.name, dct["name"])
                    self.assertEqual(project.uuid, dct["uuid"])
                    self.assertEqual(project.active, dct["active"])

            for task in t1, t2, t3:
                taskFilePath = getTaskPath(dumpDir, task)
                self.assertTrue(os.path.exists(taskFilePath))
                with open(taskFilePath) as f:
                    dct = json.load(f)
                self.assertEqual(task.title, dct["title"])
                self.assertEqual(task.project.uuid, dct["projectUuid"])
                if task.description:
                    self.assertEqual(task.description, dct["description"])

            for alias in a1, a2:
                aliasFilePath = getAliasPath(dumpDir, alias)
                self.assertTrue(os.path.exists(aliasFilePath))
                with open(aliasFilePath) as f:
                    dct = json.load(f)
                self.assertEqual(alias.name, dct["name"])
                self.assertEqual(alias.command, dct["command"])

    def testUpdateDump(self):
        t1 = dbutils.addTask("prj1", "Foo", keywordDict=dict(kw1=1, kw2=None), interactive=False)
        t2 = dbutils.addTask("prj1", "Bar", keywordDict=dict(kw1=2), interactive=False)
        t3 = dbutils.addTask("prj2", "Baz", interactive=False)

        with TemporaryDirectory() as tmpDir:
            dumpDir = os.path.join(tmpDir, "dump")
            syncManager = SyncManager(self.session, dumpDir)
            syncManager.initDumpRepository()
            syncManager.dump()

            # Do some changes: update t3, add t4, remove t2, then dump again
            newTitle = "New T3 title"
            t3.title = newTitle
            self.session.add(t3)

            t4 = dbutils.addTask("prj2", "New task", interactive=False)
            self.session.add(t4)

            self.session.delete(t2)

            self.session.commit()

            syncManager.clearDump()
            syncManager.dump()

            # Check t3 has been updated
            taskFilePath = getTaskPath(dumpDir, t3)
            with open(taskFilePath) as f:
                dct = json.load(f)
            title = dct["title"]
            self.assertEqual(title, newTitle)

            # Check t4 has been dumped
            taskFilePath = getTaskPath(dumpDir, t4)
            self.assertTrue(os.path.exists(taskFilePath))

            # Check t2 file has been removed
            taskFilePath = getTaskPath(dumpDir, t2)
            self.assertFalse(os.path.exists(taskFilePath))

    def testRemove(self):
        """Create t1 & t2. Dump the DB. Remove t1 from the DB. t1 dump should be removed,
        t2 dump should remain"""
        t1 = dbutils.addTask("prj1", "Foo", keywordDict=dict(kw1=1, kw2=None), interactive=False)
        t2 = dbutils.addTask("prj1", "Bar", keywordDict=dict(kw1=2), interactive=False)

        with TemporaryDirectory() as tmpDir:
            dumpDir = os.path.join(tmpDir, "dump")
            syncManager = SyncManager(self.session, dumpDir)
            syncManager.initDumpRepository()
            syncManager.dump()

            t1Path = getTaskPath(dumpDir, t1)
            t2Path = getTaskPath(dumpDir, t2)
            self.assertTrue(os.path.exists(t1Path))
            self.assertTrue(os.path.exists(t2Path))

            self.session.delete(t1)
            self.session.commit()

            self.assertFalse(os.path.exists(t1Path))
            self.assertTrue(os.path.exists(t2Path))
