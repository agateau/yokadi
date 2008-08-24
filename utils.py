# -*- coding: UTF-8 -*-
"""
Misc utilities. Should probably be splitted.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
from datetime import datetime

from db import *


def addTask(projectName, title, keywordDict):
    """Adds a task based on title and keywordDict.
    Returns task on success, None if cancelled."""
    # Create missing keywords
    if not createMissingKeywords(keywordDict.keys()):
        return None

    # Create missing project
    project = getOrCreateProject(projectName)
    if not project:
        return None

    # Create task
    task = Task(creationDate = datetime.now(), project=project, title=title, description="", status="new")
    task.setKeywordDict(keywordDict)
    return task


def getOrCreateKeyword(keywordName, interactive=True):
    """Returns keyword associated with keywordName, or prompt to create it if
    it does not exist. If user does not want to create it, returns None."""
    result = Keyword.selectBy(name=keywordName)
    result = list(result)
    if len(result):
        return result[0]

    while interactive:
        answer = raw_input("Keyword '%s' does not exist, create it (y/n)? " % keywordName)
        if answer == "n":
            return None
        if answer == "y":
            break
    keyword = Keyword(name=keywordName)
    print "Added keyword '%s'" % keywordName
    return keyword


def getOrCreateProject(projectName, interactive=True):
    """Returns project associated with project, or prompt to create it if it
    does not exist. If user does not want to create it, returns None."""
    result = Project.selectBy(name=projectName)
    result = list(result)
    if len(result):
        return result[0]

    while interactive:
        answer = raw_input("Project '%s' does not exist, create it (y/n)? " % projectName)
        if answer == "n":
            return None
        if answer == "y":
            break
    project = Project(name=projectName)
    print "Added project '%s'" % projectName
    return project


def createMissingKeywords(lst):
    """Create all keywords from lst which does not exist
    Returns True, if ok, False if user canceled"""
    for keywordName in lst:
        if not getOrCreateKeyword(keywordName):
            return False
    return True


def getProjectNamesStartingWith(text):
    return [x.name for x in Project.select(LIKE(Project.q.name, text + "%"))]

class YokadiException(Exception):
    """Yokadi Exceptions"""
    pass

# vi: ts=4 sw=4 et
