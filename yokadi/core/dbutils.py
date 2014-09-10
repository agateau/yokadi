# -*- coding: UTF-8 -*-
"""
Database utilities.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
from datetime import datetime, timedelta
import os

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from yokadi.ycli import tui
from yokadi.core import db
from yokadi.core.db import Keyword, Project, Task, TaskLock
from yokadi.core.yokadiexception import YokadiException


def addTask(projectName, title, keywordDict=None, interactive=True):
    """Adds a task based on title and keywordDict.
    @param projectName: name of project as a string
    @param title: task title as a string
    @param keywordDict: dictionary of keywords (name : value)
    @param interactive: Ask user before creating project (this is the default)
    @type interactive: Bool
    @returns : Task instance on success, None if cancelled."""
    session = db.getSession(
                                   )
    if keywordDict is None:
        keywordDict = {}

    # Create missing keywords
    if not createMissingKeywords(keywordDict.keys(), interactive=interactive):
        return None

    # Create missing project
    project = getOrCreateProject(projectName, interactive=interactive)
    if not project:
        return None

    # Create task
    task = Task(creationDate=datetime.now().replace(second=0, microsecond=0), project=project, title=title, description=u"", status=u"new")
    session.add(task)
    task.setKeywordDict(keywordDict)
    session.merge(task)

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


def getTaskFromId(tid):
    """Returns a task given its id, or raise a YokadiException if it does not
    exist.
    @param tid: taskId string
    @return: Task instance or None if existingTask is False"""
    session = db.getSession()
    # We do not use line.isdigit() because it returns True if line is '¹'!
    try:
        taskId = int(tid)
    except ValueError:
        raise YokadiException("task id should be a number")

    try:
        task = session.query(Task).filter_by(id=taskId).one()
    except NoResultFound:
        raise YokadiException("Task %s does not exist. Use t_list to see all tasks" % taskId)
    return task


def getOrCreateKeyword(keywordName, interactive=True):
    """Get a keyword by its name. Create it if needed
    @param keywordName: keyword name as a string
    @param interactive: Ask user before creating keyword (this is the default)
    @type interactive: Bool
    @return: Keyword instance or None if user cancel creation"""
    session = db.getSession()
    try:
        return session.query(Keyword).filter_by(name=keywordName).one()
    except (NoResultFound, MultipleResultsFound):
        if interactive and not tui.confirm("Keyword '%s' does not exist, create it" % keywordName):
            return None
        keyword = Keyword(name=keywordName)
        session.add(keyword)
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
    session = db.getSession()
    result = session.query(Project).filter_by(name=projectName).all()
    if len(result):
        return result[0]

    if not createIfNeeded:
        return None

    if interactive and not tui.confirm("Project '%s' does not exist, create it" % projectName):
        return None

    project = Project(name=projectName)
    session.add(project)
    print "Added project '%s'" % projectName
    return project


def createMissingKeywords(lst, interactive=True):
    """Create all keywords from lst which does not exist
    @param lst: list of keyword
    @return: True, if ok, False if user canceled"""
    for keywordName in lst:
        if not getOrCreateKeyword(keywordName, interactive=interactive):
            return False
    return True


def getKeywordFromName(name):
    """Returns a keyword from its name, which may start with "@"
    raises a YokadiException if not found
    @param name: the keyword name
    @return: The keyword"""
    session = db.getSession()
    if not name:
        raise YokadiException("No keyword supplied")
    if name.startswith("@"):
        name = name[1:]
    lst = session.query(Keyword).filter_by(name=name).all()
    if len(lst) == 0:
        raise YokadiException("No keyword named '%s' found" % name)
    return lst[0]


class TaskLockManager:
    """Handle a lock to prevent concurrent editing of the same task"""
    def __init__(self, task):
        """
        @param task: a Task instance
        @param session: sqlalchemy session"""
        self.task = task
        self.session = db.getSession()

    def _getLock(self):
        """Retrieve the task lock if it exists (else None)"""
        try:
            return db.getSession().query(TaskLock).filter(TaskLock.task == self.task).one()
        except NoResultFound:
            return  None

    def acquire(self):
        """Acquire a lock for that task and remove any previous stale lock"""
        lock = self._getLock()
        if lock:
            if lock.updateDate < datetime.now() - 2 * timedelta(seconds=tui.MTIME_POLL_INTERVAL):
                # Stale lock, removing
                self.session.delete(lock)
            else:
                raise YokadiException("Task %s is already locked by process %s" % (lock.task.id, lock.pid))
        self.session.add(TaskLock(task=self.task, pid=os.getpid(), updateDate=datetime.now()))
        self.session.commit()

    def update(self):
        """Update lock timestamp to avoid it to expire"""
        lock = self._getLock()
        lock.updateDate = datetime.now()
        self.session.merge(lock)
        self.session.commit()

    def release(self):
        """Release the lock for that task"""
        # Only release our lock
        lock = self._getLock()
        if lock and lock.pid == os.getpid():
            self.session.delete(lock)
            self.session.commit()

# vi: ts=4 sw=4 et
