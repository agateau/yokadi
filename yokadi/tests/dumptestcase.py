#!/usr/bin/env python3
import os
import json
import unittest

from tempfile import TemporaryDirectory

from yokadi.core import db
from yokadi.core import dbutils
from yokadi.sync import PROJECTS_DIRNAME, TASKS_DIRNAME
from yokadi.sync import dump, initDumpRepository
from yokadi.sync.gitvcsimpl import GitVcsImpl


def getTaskPath(dumpDir, task):
    return os.path.join(dumpDir, TASKS_DIRNAME, task.uuid + ".json")


def getProjectPath(dumpDir, project):
    return os.path.join(dumpDir, PROJECTS_DIRNAME, project.uuid + ".json")


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

        vcsImpl = GitVcsImpl()
        with TemporaryDirectory() as tmpDir:
            dumpDir = os.path.join(tmpDir, "dump")
            initDumpRepository(dumpDir, vcsImpl)
            dump(dumpDir, vcsImpl)

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

    def testUpdateDump(self):
        t1 = dbutils.addTask("prj1", "Foo", keywordDict=dict(kw1=1, kw2=None), interactive=False)
        t2 = dbutils.addTask("prj1", "Bar", keywordDict=dict(kw1=2), interactive=False)
        t3 = dbutils.addTask("prj2", "Baz", interactive=False)

        vcsImpl = GitVcsImpl()
        with TemporaryDirectory() as tmpDir:
            dumpDir = os.path.join(tmpDir, "dump")
            initDumpRepository(dumpDir, vcsImpl)
            dump(dumpDir, vcsImpl)

            # Do some changes: update t3, add t4, remove t2, then dump again
            newTitle = "New T3 title"
            t3.title = newTitle
            self.session.add(t3)

            t4 = dbutils.addTask("prj2", "New task", interactive=False)
            self.session.add(t4)

            self.session.delete(t2)

            self.session.commit()

            dump(dumpDir, vcsImpl)

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