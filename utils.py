from datetime import datetime

from db import *


def addTask(projectName, title, propertyDict):
    """Adds a task based on title and propertyDict.
    Returns task on success, None if cancelled."""
    # Create missing properties
    if not createMissingProperties(propertyDict.keys()):
        return None

    # Create missing project
    project = getOrCreateProject(projectName)
    if not project:
        return None

    # Create task
    task = Task(creationDate = datetime.now(), project=project, title=title, description="", status="new")
    task.setPropertyDict(propertyDict)
    return task


def getOrCreateProperty(propertyName, interactive=True):
    """Returns property associated with propertyName, or prompt to create it if
    it does not exist. If user does not want to create it, returns None."""
    result = Property.selectBy(name=propertyName)
    result = list(result)
    if len(result):
        return result[0]

    while interactive:
        answer = raw_input("Property '%s' does not exist, create it (y/n)? " % propertyName)
        if answer == "n":
            return None
        if answer == "y":
            break
    property = Property(name=propertyName)
    print "Added property '%s'" % propertyName
    return property


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


def createMissingProperties(lst):
    """Create all properties from lst which does not exist
    Returns True, if ok, False if user canceled"""
    for propertyName in lst:
        if not getOrCreateProperty(propertyName):
            return False
    return True
# vi: ts=4 sw=4 et
