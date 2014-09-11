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
# vi: ts=4 sw=4 et
