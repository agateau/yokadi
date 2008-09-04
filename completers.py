# -*- coding: UTF-8 -*-
"""
Implementation of completers for various Yokadi objects.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
import parseutils
import utils

class ProjectCompleter(object):
    def __init__(self, position):
        self.position = position


    def __call__(self, text, line, begidx, endidx):
        if parseutils.computeCompleteParameterPosition(text, line, begidx, endidx) == self.position:
            return utils.getProjectNamesStartingWith(text)
        else:
            return []


class KeywordCompleter(object):
    def __init__(self, position):
        self.position = position


    def __call__(self, text, line, begidx, endidx):
        if parseutils.computeCompleteParameterPosition(text, line, begidx, endidx) == self.position:
            return utils.getKeywordNamesStartingWith(text)
        else:
            return []

def t_listCompleter(cmd, text, line, begidx, endidx):
    if   parseutils.computeCompleteParameterPosition(text, line, begidx, endidx) == 1 : 
        return utils.getProjectNamesStartingWith(text)
    elif parseutils.computeCompleteParameterPosition(text, line, begidx, endidx) >= 2 :
        return utils.getKeywordNamesStartingWith(text)

# vi: ts=4 sw=4 et
