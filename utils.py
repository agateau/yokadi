# -*- coding: UTF-8 -*-
"""
Misc utilities. Should probably be splitted.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""
import locale
from datetime import datetime, timedelta

from sqlobject.dberrors import DuplicateEntryError
from sqlobject import LIKE, SQLObjectNotFound

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

def getTaskFromId(line, parameterName="id"):
    """Returns a task given its id, or raise a YokadiException if it does not
    exist.
    @param line: taskId string
    @param parameterName: name of the parameter to mention in exception
    @return: Task instance or None if existingTask is False"""
    line = line.strip()
    if len(line) == 0:
        raise YokadiException("Missing <%s> parameter" % parameterName)

    if not line.isdigit():
        raise YokadiException("<%s> should be a number" % parameterName)
    taskId = int(line)

    try:
        return Task.get(taskId)
    except SQLObjectNotFound:
        raise YokadiException("Task %s does not exist. Use t_list to see all tasks" % taskId)

def getProjectFromName(name, parameterName="project_name"):
    """
    Helper function which returns a project given its name, or raise a
    YokadiException if it does not exist.
    """
    name = name.strip()
    if len(name) == 0:
        raise YokadiException("Missing <%s> parameter" % parameterName)

    try:
        return Project.byName(name)
    except SQLObjectNotFound:
        raise YokadiException("Project '%s' not found. Use p_list to see all projects." % name)

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
    """Get a project by its name. Create it if needed
    @param projectName: project name as a string
    @param interactive: Ask user before creating project (this is the default)
    @type interactive: Bool
    @return: Project instance or None if user cancel creation"""
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
    @param lst: list of keyword
    @return: True, if ok, False if user canceled"""
    for keywordName in lst:
        if not getOrCreateKeyword(keywordName):
            return False
    return True

def getItemPropertiesStartingWith(item, field, text):
    """Return a list of item.field starting with text
    @param item: the object item, example : Task, Project, Keyword...
    @param field: the item's field lookup : Project.q.name, Task.q.title, Keyword.q.name. Don't forget the magic q
    @param text: The begining of the text as a str
    @return: list of matching strings"""
    return [x.name for x in item.select(LIKE(field, text + "%"))]

# vi: ts=4 sw=4 et
