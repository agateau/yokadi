# -*- coding: UTF-8 -*-
"""
TextListRenderer test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest
from StringIO import StringIO

import yokadi.ycli.colors as C
from yokadi.core import dbutils
import testutils

from yokadi.ycli import tui
from yokadi.ycli.textlistrenderer import TextListRenderer
from yokadi.core.cryptutils import YokadiCryptoManager


class TextListRendererTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        tui.clearInputAnswers()

    def testTitleFormater(self):
        dbutils.getOrCreateProject("x", interactive=False)
        dbutils.getOrCreateKeyword("k1", interactive=False)
        dbutils.getOrCreateKeyword("k2", interactive=False)
        t1 = dbutils.addTask("x", "t1", {})
        t2 = dbutils.addTask("x", "t2", {"k1": None, "k2": 12})
        longerTask = dbutils.addTask("x", "A longer task name", {})
        longerTask.description = "And it has a description"

        out = StringIO()
        renderer = TextListRenderer(out, termWidth=80, cryptoMgr=YokadiCryptoManager())
        renderer.addTaskList("Foo", [t1])
        self.assertEquals(renderer.maxTitleWidth, 5)
        renderer.end()
        expected = unicode(\
              "%(CYAN)s              Foo               %(RESET)s\n" \
            + "%(BOLD)sID|Title|U  |S|Age     |Due date%(RESET)s\n" \
            + "--------------------------------\n" \
            + "1 |t1   %(RESET)s|0  |N|0m      |        \n" \
            ) % dict(CYAN=C.CYAN, RESET=C.RESET, BOLD=C.BOLD)
        testutils.multiLinesAssertEqual(self, out.getvalue(), expected)

        out = StringIO()
        renderer = TextListRenderer(out, termWidth=80, cryptoMgr=YokadiCryptoManager())
        renderer.addTaskList("Foo", [t1, t2])
        self.assertEquals(renderer.maxTitleWidth, 11)
        renderer.end()
        expected = unicode(\
              "%(CYAN)s                 Foo                  %(RESET)s\n" \
            + "%(BOLD)sID|Title      |U  |S|Age     |Due date%(RESET)s\n" \
            + "--------------------------------------\n" \
            + "1 |t1         %(RESET)s|0  |N|0m      |        \n" \
            + "2 |t2 (%(BOLD)sk1, k2)%(RESET)s|0  |N|0m      |        \n" \
            ) % dict(CYAN=C.CYAN, RESET=C.RESET, BOLD=C.BOLD)
        testutils.multiLinesAssertEqual(self, out.getvalue(), expected)

        out = StringIO()
        renderer = TextListRenderer(out, termWidth=80, cryptoMgr=YokadiCryptoManager())
        renderer.addTaskList("Foo", [t2, longerTask])
        self.assertEquals(renderer.maxTitleWidth, len(longerTask.title) + 1)
        renderer.end()
        expected = unicode(\
              "%(CYAN)s                     Foo                      %(RESET)s\n" \
            + "%(BOLD)sID|Title              |U  |S|Age     |Due date%(RESET)s\n" \
            + "----------------------------------------------\n" \
            + "2 |t2 (%(BOLD)sk1, k2)        %(RESET)s|0  |N|0m      |        \n" \
            + "3 |A longer task name%(RESET)s*|0  |N|0m      |        \n" \
            ) % dict(CYAN=C.CYAN, RESET=C.RESET, BOLD=C.BOLD)
        testutils.multiLinesAssertEqual(self, out.getvalue(), expected)


# vi: ts=4 sw=4 et
