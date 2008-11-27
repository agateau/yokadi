# -*- coding: UTF-8 -*-
"""
Implementation of completers for various Yokadi objects.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
import parseutils
import utils
from db import Config, Keyword, Project, Task
from textrenderer import TextRenderer

class ProjectCompleter(object):
    def __init__(self, position):
        self.position = position


    def __call__(self, text, line, begidx, endidx):
        if parseutils.computeCompleteParameterPosition(text, line, begidx, endidx) == self.position:
            return utils.getItemPropertiesStartingWith(Project, Project.q.name, text)
        else:
            return []


class KeywordCompleter(object):
    def __init__(self, position):
        self.position = position


    def __call__(self, text, line, begidx, endidx):
        if parseutils.computeCompleteParameterPosition(text, line, begidx, endidx) == self.position:
            return utils.getItemPropertiesStartingWith(Keyword, Keyword.q.name, text)
        else:
            return []

def t_listCompleter(cmd, text, line, begidx, endidx):
    position=parseutils.computeCompleteParameterPosition(text, line, begidx, endidx)
    position-=len(parseutils.parseParameters(line)[0]) # remove arguments from position count
    if   position == 1 :
        return utils.getItemPropertiesStartingWith(Project, Project.q.name, text) 
    elif position >= 2 :
        return utils.getItemPropertiesStartingWith(Keyword, Keyword.q.name, text)

def confCompleter(cmd, text, line, begidx, endidx):
    return utils.getItemPropertiesStartingWith(Config, Config.q.name, text)

def taskIdCompleter(cmd, text, line, begidx, endidx):
    #TODO: filter on parameter position
    #TODO: potential performance issue with lots of tasks, find a better way to do it
    renderer=TextRenderer()
    tasks=[x for x in Task.select(Task.q.status!='done') if str(x.id).startswith(text)]
    print
    for task in tasks:
        renderer.renderTaskListRow(task)
    return [str(x.id) for x in tasks]

# vi: ts=4 sw=4 et
