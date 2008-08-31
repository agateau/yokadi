# -*- coding: UTF-8 -*-
"""
Misc utilities. Should probably be splitted.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
from datetime import datetime
from sqlobject.dberrors import DuplicateEntryError
from sqlobject import LIKE, SQLObjectNotFound
from db import Keyword, Project, Task


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
    try:
        task = Task(creationDate = datetime.now(), project=project, title=title, description="", status="new")
        task.setKeywordDict(keywordDict)
    except DuplicateEntryError:
        raise YokadiException("A task named %s already exist. Please find another name" % title)
    return task

def getTaskFromId(line, existingTask=True):
    """Verify that a taskId was provided and optionaly checks if the task exists
    @param line: taskId string
    @param existingTask: wether to check if task really exists
    @return: Task instance or None if existingTask is False"""
    if not line.isdigit():
        raise YokadiException("Provide a task id")
    taskId = int(line)
    if existingTask:
        try:
            task = Task.get(taskId)
        except SQLObjectNotFound:
            raise YokadiException("Task %s does not exist. Use t_list to see all tasks" % taskId)
    else:
        task=None
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

def guessDateFormat(tDate):
    """Guess and return format of date as a string"""
    if tDate.count("/")==2:
        fDate="%d/%m/%Y"
    elif tDate.count("/")==1:
        fDate="%d/%m"
    else:
        fDate="%d"
    return fDate

def guessTimeFormat(tTime):
    """Guess and return format of time as a string"""
    if tTime.count(":")==2:
        fTime="%H:%M:%S"
    elif tTime.count(":")==1:
        fTime="%H:%M"
    else:
        fTime="%H"
    return fTime

class YokadiException(Exception):
    """Yokadi Exceptions"""
    pass

# vi: ts=4 sw=4 et
