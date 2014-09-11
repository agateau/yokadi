# -*- coding: UTF-8 -*-
"""
Database access layer using SQL Alchemy

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""

import os
import sys
from pickle import loads, dumps
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, Boolean, Unicode, DateTime, Enum, ForeignKey


try:
    from dateutil import rrule
except ImportError:
    print("You must install python-dateutil to use Yokadi")
    print("This library is used for task recurrence")
    print("Use 'pip install python-dateutil'")
    sys.exit(1)

from yokadi.core.yokadiexception import YokadiException
from yokadi.ycli import tui  # TODO: try to remove dependancy on tui
from yokadi.core import utils

# Yokadi database version needed for this code
# If database config key DB_VERSION differs from this one a database migration
# is required
DB_VERSION = 7
DB_VERSION_KEY = u"DB_VERSION"

# Task frequency
FREQUENCY = {0: "Yearly", 1: "Monthly", 2: "Weekly", 3: "Daily"}

Base = declarative_base()


class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)
    active = Column(Boolean, default=True)
    projectKeywords = relationship("ProjectKeyword", backref="project")

    def __repr__(self):
        keywords = self.getKeywordsAsString()
        if keywords:
            return "%s (%s)" % (self.name, keywords)
        else:
            return self.name

    def setKeywordDict(self, dct):
        """
        Defines keywords of a project.
        Dict is of the form: keywordName => value
        """
        session = getSession()
        for projectKeyword in self.projectKeywords:
            session.delete(projectKeyword)

        for name, value in list(dct.items()):
            keyword = session.query(Keyword).filter_by(name=name).one()
            session.add(ProjectKeyword(project=self, keyword=keyword, value=value))

    def getKeywordDict(self):
        """
        Returns all keywords of a project as a dict of the form:
        keywordName => value
        """
        dct = {}
        for projectKeyword in self.projectKeywords:
            dct[projectKeyword.keyword.name] = projectKeyword.value
        return dct

    def getKeywordsAsString(self):
        """
        Returns all keywords as a string like "key1=value1, key2=value2..."
        Value is not displayed if none
        """
        result = []
        for key, value in list(self.getKeywordDict().items()):
            if value:
                result.append("%s=%s" % (key, value))
            else:
                result.append(key)
        return ", ".join(result)


class Keyword(Base):
    __tablename__ = "keyword"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)
    tasks = association_proxy("taskKeywords", "task")

    def __repr__(self):
        return self.name

    def getTasks(self):
        return [taskKeyword.task for taskKeyword in self.taskKeywords]


class TaskKeyword(Base):
    __tablename__ = "task_keyword"
    id = Column(Integer, primary_key=True)
    taskId = Column("task_id", Integer, ForeignKey("task.id"))
    keywordId = Column("keyword_id", Integer, ForeignKey("keyword.id"))
    value = Column(Integer, default=None)
    keyword = relationship("Keyword", backref="taskKeywords")


class ProjectKeyword(Base):
    __tablename__ = "project_keyword"
    id = Column(Integer, primary_key=True)
    projectId = Column("project_id", Integer, ForeignKey("project.id"))
    keywordId = Column("keyword_id", Integer, ForeignKey("keyword.id"))
    value = Column(Integer, default=None)
    keyword = relationship("Keyword", backref="projectKeywords")


class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    creationDate = Column("creation_date", DateTime, nullable=False)
    dueDate = Column("due_date", DateTime, default=None)
    doneDate = Column("done_date", DateTime, default=None)
    description = Column(Unicode, default="", nullable=False)
    urgency = Column(Integer, default=0, nullable=False)
    status = Column(Enum("new", "started", "done"), default="new")
    projectId = Column("project_id", Integer, ForeignKey("project.id"))
    project = relationship("Project", backref="tasks")
    taskKeywords = relationship("TaskKeyword", backref="task")
    recurrenceId = Column("recurrence_id", Integer, ForeignKey("recurrence.id"), default=None)
    recurrence = relationship("Recurrence")

    def setKeywordDict(self, dct):
        """
        Defines keywords of a task.
        Dict is of the form: keywordName => value
        """
        session = getSession()
        for taskKeyword in self.taskKeywords:
            session.delete(taskKeyword)

        for name, value in list(dct.items()):
            keyword = session.query(Keyword).filter_by(name=name).one()
            session.add(TaskKeyword(task=self, keyword=keyword, value=value))

    def getKeywordDict(self):
        """
        Returns all keywords of a task as a dict of the form:
        keywordName => value
        """
        dct = {}
        for taskKeyword in self.taskKeywords:
            dct[taskKeyword.keyword.name] = taskKeyword.value
        return dct

    def getKeywordsAsString(self):
        """
        Returns all keywords as a string like "key1=value1, key2=value2..."
        """
        return ", ".join(list(("%s=%s" % k for k in list(self.getKeywordDict().items()))))

    def getUserKeywordsNameAsString(self):
        """
        Returns all keywords keys as a string like "key1, key2, key3...".
        Internal keywords (starting with _) are ignored.
        """
        keywords = [k for k in list(self.getKeywordDict().keys()) if not k.startswith("_")]
        keywords.sort()
        if keywords:
            return ", ".join(keywords)
        else:
            return ""


class Recurrence(Base):
    """Task recurrence definition"""
    __tablename__ = "recurrence"
    id = Column(Integer, primary_key=True)
    rule = Column(Unicode, default="")

    def getRrule(self):
        """Create rrule object from its Recurrence representation
        @return: dateutil.rrule.rrule instance"""
        return loads(self.rule)

    def setRrule(self, rule):
        """Set Recurrence according to rule
        @type rule: dateutil.rrule.rrule instance"""
        self.rule = dumps(rule)

    def getNext(self, refDate=None):
        """Return next date of recurrence after given date
        @param refDate: reference date used to compute the next occurence of recurrence
        @type refDate: datetime
        @return: next occurence (datetime)"""
        rr = self.getRrule()
        if refDate is None:
            refDate = datetime.now().replace(second=0, microsecond=0)
        return rr.after(refDate)

    def __str__(self):
        return "%s (next: %s)" % (FREQUENCY[self.getRrule()._freq], self.getNext())


class Config(Base):
    """yokadi config"""
    __tablename__ = "config"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)
    value = Column(Unicode)
    system = Column(Boolean)
    desc = Column(Unicode)


class TaskLock(Base):
    __tablename__ = "task_lock"
    id = Column(Integer, primary_key=True)
    taskId = Column("task_id", Integer, ForeignKey("task.id"), unique=True)
    task = relationship("Task")
    pid = Column(Integer, default=None)
    updateDate = Column("update_date", DateTime, default=None)


def getConfigKey(name, environ=True):
    session = getSession()
    if environ:
        return os.environ.get(name, session.query(Config).filter_by(name=name).one().value)
    else:
        return session.query(Config).filter_by(name=name).one().value


_database = None

def getSession():
    global _database
    if not _database:
        raise YokadiException("Cannot get session. Not connected to database")
    return _database.session

def connectDatabase(dbFileName, createIfNeeded=True, memoryDatabase=False):
    global _database
    _database = Database(dbFileName, createIfNeeded, memoryDatabase)


class Database(object):
    def __init__(self, dbFileName, createIfNeeded=True, memoryDatabase=False, updateMode=False):
        """Connect to database and create it if needed
        @param dbFileName: path to database file
        @type dbFileName: str
        @param createIfNeeded: Indicate if database must be created if it does not exists (default True)
        @type createIfNeeded: bool
        @param memoryDatabase: create db in memory. Only usefull for unit test. Default is false.
        @type memoryDatabase: bool
        @param updateMode: allow to use it without checking version. Default is false.
        @type updateMode: bool
        """

        dbFileName = os.path.abspath(dbFileName)

        if sys.platform == 'win32':
            connectionString = 'sqlite://' + dbFileName[0] + '|' + dbFileName[2:]
        else:
            connectionString = 'sqlite:///' + dbFileName

        if memoryDatabase:
            connectionString = "sqlite:///:memory:"

        self.engine = create_engine(connectionString)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        if not os.path.exists(dbFileName) or memoryDatabase:
            if createIfNeeded:
                print("Creating database")
                self.createTables()
                # Set database version according to current yokadi release
                if not updateMode: # Update script add it from dump
                    self.session.add(Config(name=DB_VERSION_KEY, value=str(DB_VERSION), system=True, desc="Database schema release number"))
                self.session.commit()
            else:
                print("Database file (%s) does not exist or is not readable. Exiting" % dbFileName)
                sys.exit(1)

        if not updateMode:
            self.checkVersion()

    def createTables(self):
        """Create all defined tables"""
        Base.metadata.create_all(self.engine)

    def getVersion(self):
        if not self.engine.has_table("config"):
            # There was no Config table in v1
            return 1

        try:
            return int(self.session.query(Config).filter_by(name=DB_VERSION_KEY).one().value)
        except NoResultFound:
            raise YokadiException("Configuration key '%s' does not exist. This should not happen!" % DB_VERSION_KEY)

    def setVersion(self, version):
        assert self.engine.has_table("config")
        instance = self.session.query(Config).filter_by(name=DB_VERSION_KEY).one()
        instance.value = str(version)
        self.session.add(instance)
        self.session.commit()

    def checkVersion(self):
        """Check version and exit if it is not suitable"""
        version = self.getVersion()
        if version != DB_VERSION:
            sharePath = os.path.abspath(utils.shareDirPath())
            tui.error("Your database version is %d but Yokadi wants version %d." \
                % (version, DB_VERSION))
            print("Please, run the %s/update/update.py script to migrate your database prior to running Yokadi" % \
                    sharePath)
            print("See %s/update/README.markdown for details" % sharePath)
            sys.exit(1)


def setDefaultConfig():
    """Set default config parameter in database if they (still) do not exist"""
    defaultConfig = {
        "ALARM_DELAY_CMD" : ('''kdialog --passivepopup "task {TITLE} ({ID}) is due for {DATE}" 180 --title "Yokadi: {PROJECT}"''', False,
                             "Command executed by Yokadi Daemon when a tasks due date is reached soon (see ALARM_DELAY"),
        "ALARM_DUE_CMD"   : ('''kdialog --passivepopup "task {TITLE} ({ID}) should be done now" 1800 --title "Yokadi: {PROJECT}"''', False,
                             "Command executed by Yokadi Daemon when a tasks due date is reached soon (see ALARM_DELAY"),
        "ALARM_DELAY"     : ("8", False, "Delay (in hours) before due date to launch the alarm (see ALARM_CMD)"),
        "ALARM_SUSPEND"   : ("1", False, "Delay (in hours) before an alarm trigger again"),
        "PURGE_DELAY"     : ("90", False, "Default delay (in days) for the t_purge command"),
        "PASSPHRASE_CACHE": ("1", False, "Keep passphrase in memory till Yokadi is started (0 is false else true"),
        }

    session = getSession()
    for name, value in defaultConfig.items():
        if session.query(Config).filter_by(name=name).count() == 0:
            session.add(Config(name=name, value=value[0], system=value[1], desc=value[2]))

# vi: ts=4 sw=4 et
