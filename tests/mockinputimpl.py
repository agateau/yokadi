# -*- coding: UTF-8 -*-
"""
Mock implementation of raw_input which allows to supply predefined answers.
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
class MockInputImpl(object):
    def __init__(self, *answers):
        self.answers = list(answers)

    def __call__(self, prompt):
        return self.answers.pop(0)
# vi: ts=4 sw=4 et
