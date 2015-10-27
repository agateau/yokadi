# -*- coding: UTF-8 -*-
"""
Utils for unit-test
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""


def multiLinesAssertEqual(test, str1, str2):
    lst1 = str1.splitlines()
    lst2 = str2.splitlines()
    for row, lines in enumerate(zip(lst1, lst2)):
        line1, line2 = lines
        test.assertEqual(line1, line2, "Error line %d:\n%r\n!=\n%r" % (row + 1, line1, line2))
    test.assertEqual(len(lst1), len(lst2))


class TestRenderer(object):
    """
    A fake renderer, which stores all rendered tasks in taskDict
    """
    def __init__(self):
        self.taskDict = {}

    def addTaskList(self, sectionName, taskList):
        self.taskDict[sectionName] = taskList

    def end(self):
        pass
# vi: ts=4 sw=4 et
