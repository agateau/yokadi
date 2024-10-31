# -*- coding: UTF-8 -*-
"""
TextListRenderer test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import unittest
from io import StringIO

from yokadi.ycli import colors
from yokadi.core import dbutils

from yokadi.ycli import tui
from yokadi.ycli.textlistrenderer import TextListRenderer, TitleFormater
from yokadi.core import db


def stripColor(text):
    for colorcode in (colors.BOLD, colors.RED, colors.GREEN, colors.ORANGE, colors.PURPLE, colors.CYAN, colors.GREY,
                      colors.RESET):
        text = text.replace(colorcode, '')
    return text


class TextListRendererTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()
        tui.clearInputAnswers()

    def testTitleFormater(self):
        dbutils.getOrCreateProject("x", interactive=False)
        dbutils.getOrCreateKeyword("key1", interactive=False)
        dbutils.getOrCreateKeyword("key2", interactive=False)
        task = dbutils.addTask("x", "t1", {})
        taskWithKeywords = dbutils.addTask("x", "t2", {"key1": None, "key2": 12})

        longTask = dbutils.addTask("x", "01234567890123456789", {})
        longTask.description = "And it has a description"

        TEST_DATA = (
            (task, 20, "t1"),
            (taskWithKeywords, 20, "t2 @key1 @key2"),
            (taskWithKeywords, 4, "t2 >"),
            (longTask, 10, longTask.title[:8] + ">*"),
            (longTask, len(longTask.title), longTask.title[:-2] + ">*"),
            (longTask, len(longTask.title) + 1, longTask.title + "*"),
            (longTask, 40, longTask.title.ljust(39) + "*"),
        )

        for task, width, expected in TEST_DATA:
            with self.subTest(task=task, width=width):
                formater = TitleFormater(width)
                out = formater(task)[0]
                out = stripColor(out)

                expected = expected.ljust(width)
                self.assertEqual(out, expected)

    def testFullRendering(self):
        dbutils.getOrCreateProject("x", interactive=False)
        dbutils.getOrCreateKeyword("k1", interactive=False)
        dbutils.getOrCreateKeyword("k2", interactive=False)
        dbutils.addTask("x", "t1", {})
        t2 = dbutils.addTask("x", "t2", {"k1": None, "k2": 12})
        longTask = dbutils.addTask("x", "A longer task name", {})
        longTask.description = "And it has a description"

        out = StringIO()
        renderer = TextListRenderer(out, termWidth=80)
        renderer.addTaskList("Foo", [t2, longTask])
        self.assertEqual(renderer.maxTitleWidth, len(longTask.title) + 1)
        renderer.end()
        out = stripColor(out.getvalue())

        expected = \
            "                     Foo                      \n" \
            "ID│Title              │U  │S│Age     │Due date\n" \
            "──┼───────────────────┼───┼─┼────────┼────────\n" \
            "2 │t2 @k1 @k2         │0  │N│0m      │        \n" \
            "3 │A longer task name*│0  │N│0m      │        \n"
        self.assertMultiLineEqual(out, expected)


# vi: ts=4 sw=4 et
