# -*- coding: UTF-8 -*-
"""
Task test cases
@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import unittest
from unittest.mock import patch

import testutils

from yokadi.ycli import tui
from yokadi.ycli.main import YokadiCmd
from yokadi.core import db
from yokadi.core import dbutils
from yokadi.core.db import Task, TaskLock, Keyword, setDefaultConfig, Project, TaskKeyword
from yokadi.core.yokadiexception import YokadiException, BadUsageException


class TaskTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        setDefaultConfig()
        self.session = db.getSession()
        tui.clearInputAnswers()
        self.cmd = YokadiCmd()

    def testAdd(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")

        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x @kw1 @kw2=12 t2")

        tui.addInputAnswers("n")
        self.cmd.do_t_add("notExistingProject newTask")

        tasks = self.session.query(Task).all()
        result = [x.title for x in tasks]
        expected = ["t1", "t2"]
        self.assertEqual(result, expected)

        kwDict = self.session.get(Task, 2).getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))

        for bad_input in ("",  # No project
                          "x"):  # No task name
            self.assertRaises(BadUsageException, self.cmd.do_t_add, bad_input)

    def testEdit(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x txt @_note")

        tui.addInputAnswers("newtxt")
        self.cmd.do_t_edit("1")

        task = self.session.get(Task, 1)
        self.assertEqual(task.title, "newtxt")
        self.assertEqual(task.getKeywordDict(), {"_note": None})

    def testEditAddKeyword(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x txt")

        tui.addInputAnswers("txt @kw", "y")
        self.cmd.do_t_edit("1")

        task = self.session.get(Task, 1)
        self.assertEqual(task.title, "txt")
        self.assertEqual(task.getKeywordDict(), {"kw": None})

    def testEditRemoveKeyword(self):
        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x txt @kw")

        tui.addInputAnswers("txt")
        self.cmd.do_t_edit("1")

        task = self.session.get(Task, 1)
        self.assertEqual(task.title, "txt")
        self.assertEqual(task.getKeywordDict(), {})

    def testRemove(self):
        # Create a recurrent task with one keyword
        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x @kw bla")
        task = self.session.query(Task).one()
        self.cmd.do_t_recurs("1 daily 10:00")

        keyword = self.session.query(Keyword).filter_by(name="kw").one()
        self.assertEqual(keyword.tasks, [task])

        # Pretend we edit the task description so that we have a TaskLock for
        # this task
        taskLockManager = dbutils.TaskLockManager(task)
        taskLockManager.acquire()
        self.session.query(TaskLock).one()
        self.assertEqual(self.session.query(TaskLock).count(), 1)

        # Remove it, the keyword should no longer be associated with any task,
        # the lock should be gone
        tui.addInputAnswers("y")
        self.cmd.do_t_remove(str(task.id))

        self.assertEqual(keyword.tasks, [])
        self.assertEqual(self.session.query(TaskLock).count(), 0)

        # Should not crash
        taskLockManager.release()

    def testMark(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task = self.session.get(Task, 1)
        self.assertEqual(task.status, "new")
        self.cmd.do_t_mark_started("1")
        self.assertEqual(task.status, "started")
        self.cmd.do_t_mark_new("1")
        self.assertEqual(task.status, "new")
        self.cmd.do_t_mark_done("1")
        self.assertEqual(task.status, "done")

    def testAddKeywords(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task = self.session.get(Task, 1)

        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add_keywords("1 @kw1 @kw2=12")

        kwDict = task.getKeywordDict()
        self.assertEqual(kwDict, dict(kw1=None, kw2=12))

        for bad_input in ("",  # No task
                          "1",  # No keyword
                          "1 kw1"):  # No @ before kw1
            self.assertRaises(YokadiException, self.cmd.do_t_add_keywords, bad_input)

    def testSetProject(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        tui.addInputAnswers("y")
        self.cmd.do_t_project("1 y")
        task1 = self.session.get(Task, 1)
        self.assertEqual(task1.project.name, "y")

        self.cmd.do_t_add("x t2")
        self.cmd.do_t_project("1 _")
        task1 = self.session.get(Task, 1)
        self.assertEqual(task1.project.name, "x")

        tui.addInputAnswers("n")
        self.cmd.do_t_project("1 doesnotexist")
        task1 = self.session.get(Task, 1)
        self.assertEqual(task1.project.name, "x")

    def testLastTaskId(self):
        # Using "_" with no prior task activity should raise an exception
        self.assertRaises(YokadiException, self.cmd.getTaskFromId, "_")

        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task1 = self.session.get(Task, 1)
        self.assertEqual(self.cmd.getTaskFromId("_"), task1)

        self.cmd.do_t_add("x t2")
        task2 = self.session.get(Task, 2)
        self.assertEqual(self.cmd.getTaskFromId("_"), task2)

        self.cmd.do_t_mark_started("1")
        self.assertEqual(self.cmd.getTaskFromId("_"), task1)

    def testLastProjectName(self):
        # Using "_" with no prior project used should raise an exception
        self.assertRaises(YokadiException, self.cmd.do_t_add, "_ t1")
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task1 = self.session.get(Task, 1)
        self.cmd.do_t_add("_ t2")
        task2 = self.session.get(Task, 2)
        self.assertEqual(task1.project, task2.project)

    def testRecurs(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        task = self.session.get(Task, 1)

        self.cmd.do_t_recurs("1 daily 10:00")
        self.assertTrue(task.recurrence)
        self.assertEqual(task.status, "new")
        self.cmd.do_t_mark_done("1")

        self.assertEqual(task.status, "new")

        self.cmd.do_t_recurs("1 none")
        self.assertFalse(task.recurrence)

        self.cmd.do_t_mark_done("1")
        self.assertEqual(task.status, "done")

        for bad_input in ("",  # No task
                          "1",  # No recurence
                          "1 foo",  # Unknown recurrence
                          "1 daily",  # No time
                          "1 weekly",  # No day
                          "1 weekly monday",  # No time
                          "1 monthly",  # No day
                          "1 monthly 10",  # No time
                          "1 quarterly",  # No day
                          "1 quarterly 10",  # No time
                          "1 monthly foo 12:00",  # Bad date
                          ):
            self.assertRaises(YokadiException, self.cmd.do_t_recurs, bad_input)

    def testRenderListSectionOrder(self):
        projectNames = "ccc", "aaa", "UPPER_CASE", "zzz", "mmm"
        projectList = []
        for name in projectNames:
            prj = Project(name=name)
            task = Task(project=prj, title="Hello")
            self.session.add(prj)
            self.session.add(task)
            projectList.append(prj)
        self.session.flush()

        renderer = testutils.TestRenderer()
        self.cmd._renderList(renderer, projectList, filters=[], order=[])

        self.assertEqual(list(renderer.taskDict.keys()), sorted(projectNames, key=lambda x: x.lower()))

    def testRenderListSectionOrderKeywords(self):
        prj = Project(name="prj")
        keywordNames = ["kw_" + x for x in ("ccc", "aaa", "UPPER_CASE", "zzz", "mmm")]
        keywordList = []
        for name in keywordNames:
            keyword = Keyword(name=name)
            task = Task(project=prj, title="Hello")
            TaskKeyword(task=task, keyword=keyword)
            self.session.add(task)
            keywordList.append(prj)
        self.session.flush()

        renderer = testutils.TestRenderer()
        self.cmd._renderList(renderer, [prj], filters=[], order=[], groupKeyword="kw_%")

        self.assertEqual(list(renderer.taskDict.keys()), sorted(keywordNames, key=lambda x: x.lower()))

    def testTlist(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        tui.addInputAnswers("y", "y")
        self.cmd.do_t_add("x @kw1 @kw2=12 t2")

        for line in ("", "-a", "-t", "-d today", "-u 10", "-k %", "-k _%", "-s t", "--overdue",
                     "@%", "@k%", "!@%", "!@kw1", "-f plain", "-f xml", "-f html", "-f csv"):
            self.cmd.do_t_list(line)

    def testTlistUrgency0(self):
        # Given a project with two tasks, one with a negative urgency
        prj = Project(name="prj")
        self.session.add(prj)
        t1 = Task(project=prj, title="t1")
        self.session.add(t1)
        t2 = Task(project=prj, title="t2", urgency=-1)
        self.session.add(t2)
        self.session.flush()
        # When I list tasks with -u 0
        renderer = testutils.TestRenderer()
        self.cmd.do_t_list("-u 0", renderer=renderer)
        # Then the task with a negative urgency is not listed
        self.assertEqual(renderer.tasks, [t1])

    def testNlist(self):
        tui.addInputAnswers("y")
        self.cmd.do_n_add("x t1")
        self.cmd.do_t_add("x t2")
        tui.addInputAnswers("y", "y")
        self.cmd.do_n_add("x @kw1 @kw2=12 t3")
        self.cmd.do_t_add("x @kw1 @kw2=12 t4")

        for line in ("", "-k %", "-k _%", "-s t",
                     "@%", "@k%", "!@%", "!@kw1", "-f plain"):
            self.cmd.do_t_list(line)

    def testTfilter(self):
        t1 = dbutils.addTask("x", "t1", interactive=False)
        t2 = dbutils.addTask("x", "t2", keywordDict={"kw1": None, "kw2": 12}, interactive=False)
        t3 = dbutils.addTask("y", "t3", interactive=False)

        testData = [
            ("@kw1", {"x": [t2]}),
            ("@kw1 @kw2", {"x": [t2]}),
            ("x", {"x": [t1, t2]}),
            ("x @kw1", {"x": [t2]}),
            ("none", {"x": [t1, t2], "y": [t3]}),
        ]
        for filter, expectedTaskDict in testData:
            self.cmd.do_t_filter(filter)
            renderer = testutils.TestRenderer()
            self.cmd.do_t_list("", renderer=renderer)
            self.assertEqual(renderer.taskDict.keys(), expectedTaskDict.keys())
            for key in renderer.taskDict.keys():
                self.assertEqual([x.title for x in renderer.taskDict[key]], [x.title for x in expectedTaskDict[key]])

        self.assertRaises(YokadiException, self.cmd.do_t_filter, "")

    def testTApply(self):
        self.cmd.do_k_add("lala")
        for i in range(10):
            tui.addInputAnswers("y")
            self.cmd.do_t_add("x t%s" % i)
        ids = [1, 2, 4, 5, 6, 9]
        self.cmd.do_t_apply("1 2,4-6 9 t_add_keywords @lala")
        for taskId in range(1, 10):
            kwDict = self.session.get(Task, taskId).getKeywordDict()
            if taskId in ids:
                self.assertEqual(kwDict, dict(lala=None))
            else:
                self.assertNotEqual(kwDict, dict(lala=None))

        # raise error if t_list had not been called previously
        self.assertRaises(BadUsageException, self.cmd.do_t_apply, "__ t_add_keywords @toto")

        self.cmd.do_t_list("@lala")
        self.cmd.do_t_apply("__ t_add_keywords @toto")
        for taskId in range(1, 10):
            kwDict = self.session.get(Task, taskId).getKeywordDict()
            if taskId in ids:
                self.assertEqual(kwDict, dict(lala=None, toto=None))
            else:
                self.assertNotEqual(kwDict, dict(lala=None, toto=None))

    def testReorderFailsOnInvalidInputs(self):
        self.assertRaises(BadUsageException, self.cmd.do_t_reorder, "unknown_project")
        self.assertRaises(BadUsageException, self.cmd.do_t_reorder, "too much args")

    def testDue(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")
        for valid_input in ("+1d", "+1m"):
            self.cmd.do_t_due("1 %s" % valid_input)
        for bad_input in ("coucou", "+1s"):
            self.assertRaises(YokadiException, self.cmd.do_t_due, "1 %s" % bad_input)

    def testToNote(self):
        tui.addInputAnswers("y")
        self.cmd.do_t_add("x t1")

        self.cmd.do_t_to_note(1)
        task = self.session.get(Task, 1)
        self.assertTrue(task.isNote(self.session))

        # Doing it twice should not fail
        self.cmd.do_t_to_note(1)
        task = self.session.get(Task, 1)
        self.assertTrue(task.isNote(self.session))

    def testToTask(self):
        tui.addInputAnswers("y")
        self.cmd.do_n_add("x t1")

        self.cmd.do_n_to_task(1)
        task = self.session.get(Task, 1)
        self.assertFalse(task.isNote(self.session))

        # Doing it twice should not fail
        self.cmd.do_n_to_task(1)
        task = self.session.get(Task, 1)
        self.assertFalse(task.isNote(self.session))

    @patch("yokadi.ycli.tui.editText")
    def testReorder(self, editTextMock):
        t1, t2, t3 = [dbutils.addTask("x", f"t{x}", interactive=False) for x in range(1, 4)]

        # Simulate moving t3 from 3rd line to the 1st
        editTextMock.return_value = "3,t3\n1,t1\n2,t2"

        self.cmd.do_t_reorder("x")
        editTextMock.assert_called_with("1,t1\n2,t2\n3,t3")

        self.assertEqual(t3.urgency, 2)
        self.assertEqual(t1.urgency, 1)
        self.assertEqual(t2.urgency, 0)

# vi: ts=4 sw=4 et
