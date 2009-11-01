# -*- coding: UTF-8 -*-
"""
Database utilities.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
from datetime import datetime

from sqlobject.dberrors import DuplicateEntryError
from sqlobject import SQLObjectNotFound

import tui
from db import Keyword, Project, Task
from yokadiexception import YokadiException


def addTask(projectName, title, keywordDict):
    """Adds a task based on title and keywordDict.
    @param projectName: name of project as a string
    @param title: task title as a string
    @param keywordDict: dictionary of keywords (name : value)
    @returns : Task instance on success, None if cancelled."""

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
        raise YokadiException("A task named %s already exists in this project. Please find another name" % title)

    return task

def updateTask(task, projectName, title, keywordDict):
    """
    Update an existing task, returns True if it went well, False if user
    canceled the update
    """
    if not createMissingKeywords(keywordDict.keys()):
        return False

    project = getOrCreateProject(projectName)
    if not project:
        return False

    task.project = project
    task.title = title
    task.setKeywordDict(keywordDict)
    return True


def getTaskFromId(line, parameterName="id"):
    """Returns a task given its id, or raise a YokadiException if it does not
    exist.
    @param line: taskId string
    @param parameterName: name of the parameter to mention in exception
    @return: Task instance or None if existingTask is False"""

    line = line.strip()
    if len(line) == 0:
        raise YokadiException("Missing <%s> parameter" % parameterName)

    # We do not use line.isdigit() because it returns True if line is '¹'!
    try:
        taskId = int(line)
    except ValueError:
        raise YokadiException("<%s> should be a number" % parameterName)

    try:
        task = Task.get(taskId)
    except SQLObjectNotFound:
        raise YokadiException("Task %s does not exist. Use t_list to see all tasks" % taskId)
    return task

#TODO: factorize the two following functions and make a generic one
def getOrCreateKeyword(keywordName, interactive=True):
    """Get a keyword by its name. Create it if needed
    @param keywordName: keyword name as a string
    @param interactive: Ask user before creating keyword (this is the default)
    @type interactive: Bool
    @return: Keyword instance or None if user cancel creation"""
    result = Keyword.selectBy(name=keywordName)
    result = list(result)
    if len(result):
        return result[0]

    if interactive and not tui.confirm("Keyword '%s' does not exist, create it" % keywordName):
        return None
    keyword = Keyword(name=keywordName)
    print "Added keyword '%s'" % keywordName
    return keyword


def getOrCreateProject(projectName, interactive=True, createIfNeeded=True):
    """Get a project by its name. Create it if needed
    @param projectName: project name as a string
    @param interactive: Ask user before creating project (this is the default)
    @type interactive: Bool
    @param createIfNeeded: create project if it does not exist (this is the default)
    @type createIfNeeded: Bool
    @return: Project instance or None if user cancel creation or createIfNeeded is False"""
    result = Project.selectBy(name=projectName)
    result = list(result)
    if len(result):
        return result[0]

    if not createIfNeeded:
        return None

    if interactive and not tui.confirm("Project '%s' does not exist, create it" % projectName):
        return None

    project = Project(name=projectName)
    print "Added project '%s'" % projectName
    return project


def createMissingKeywords(lst):
    """Create all keywords from lst which does not exist
    @param lst: list of keyword
    @return: True, if ok, False if user canceled"""
    for keywordName in lst:
        if not getOrCreateKeyword(keywordName):
            return False
    return True

# vi: ts=4 sw=4 et
