from datetime import datetime
import os
import readline
import subprocess
import tempfile

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


def editText(text):
    """Edit text with external editor
    returns a tuple (success, newText)"""
    (fd, name) = tempfile.mkstemp(suffix=".txt", prefix="yokadi-")
    try:
        fl = file(name, "w")
        fl.write(text)
        fl.close()
        retcode = subprocess.call(["vim", name])
        if retcode != 0:
            return (False, text)
        newText = file(name).read()
        return (True, newText)
    finally:
        os.close(fd)
        os.unlink(name)


def editLine(line, prompt="edit> "):
    """Edit a line using readline"""
    # Init readline
    # (Code copied from yagtd)
    def pre_input_hook():
        readline.insert_text(line)
        readline.redisplay()

        # Unset the hook again
        readline.set_pre_input_hook(None)

    readline.set_pre_input_hook(pre_input_hook)

    line = raw_input(prompt)
    # Remove edited line from history:
    #   oddly, get_history_item is 1-based,
    #   but remove_history_item is 0-based
    length = readline.get_current_history_length()
    if length > 0:
        readline.remove_history_item(length - 1)

    return line
# vi: ts=4 sw=4 et
