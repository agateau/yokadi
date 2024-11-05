# -*- coding: UTF-8 -*-
"""
Database access layer using SQL Alchemy

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""

import json
import os
from datetime import datetime
from uuid import uuid1

from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, Integer, Boolean, Unicode, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.types import TypeDecorator, VARCHAR

from yokadi.core.recurrencerule import RecurrenceRule
from yokadi.core.yokadiexception import YokadiException

# Yokadi database version needed for this code
# If database config key DB_VERSION differs from this one a database migration
# is required
DB_VERSION = 12
DB_VERSION_KEY = "DB_VERSION"


class DbUserException(Exception):
    """
    This exception is for errors which are not caused by a failure in our code
    and which must be fixed by the user.
    """
    pass


Base = declarative_base()


NOTE_KEYWORD = "_note"


def uuidGenerator():
    return str(uuid1())


class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    uuid = Column(Unicode, unique=True, default=uuidGenerator, nullable=False)
    name = Column(Unicode, unique=True)
    active = Column(Boolean, default=True)
    tasks = relationship("Task", cascade="all", backref="project", cascade_backrefs=False)

    def __repr__(self):
        return self.name

    def merge(self, session, other):
        """Merge other into us

        This function calls session.commit() itself: we have to commit after
        moving the tasks but *before* deleting `other` otherwise when we delete
        `other` SQLAlchemy deletes its former tasks as well because it thinks
        they are still attached to `other`"""
        if self is other:
            raise YokadiException("Cannot merge a project into itself")

        for task in other.tasks:
            task.projectId = self.id

        session.commit()

        session.delete(other)
        session.commit()


class Keyword(Base):
    __tablename__ = "keyword"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)
    tasks = association_proxy("taskKeywords", "task")
    taskKeywords = relationship("TaskKeyword", cascade="all", backref="keyword", cascade_backrefs=False)

    def __repr__(self):
        return self.name


class TaskKeyword(Base):
    __tablename__ = "task_keyword"
    __mapper_args__ = {"confirm_deleted_rows": False}
    id = Column(Integer, primary_key=True)
    taskId = Column("task_id", Integer, ForeignKey("task.id"), nullable=False)
    keywordId = Column("keyword_id", Integer, ForeignKey("keyword.id"), nullable=False)
    value = Column(Integer, default=None)

    __table_args__ = (
        UniqueConstraint("task_id", "keyword_id", name="task_keyword_uc"),
    )

    def __repr__(self):
        return "<TaskKeyword task={} keyword={} value={}>".format(self.task, self.keyword, self.value)


class RecurrenceRuleColumnType(TypeDecorator):
    """Represents an ydateutils.RecurrenceRule column
    """
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value:
            value = json.dumps(value.toDict())
        else:
            value = ""
        return value

    def process_result_value(self, value, dialect):
        if value:
            dct = json.loads(value)
            value = RecurrenceRule.fromDict(dct)
        else:
            value = RecurrenceRule()
        return value


class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True)
    uuid = Column(Unicode, unique=True, default=uuidGenerator, nullable=False)
    title = Column(Unicode)
    creationDate = Column("creation_date", DateTime, nullable=False, default=datetime.now)
    dueDate = Column("due_date", DateTime, default=None)
    doneDate = Column("done_date", DateTime, default=None)
    description = Column(Unicode, default="", nullable=False)
    urgency = Column(Integer, default=0, nullable=False)
    status = Column(Enum("new", "started", "done"), default="new")
    recurrence = Column(RecurrenceRuleColumnType, nullable=False, default=RecurrenceRule())
    projectId = Column("project_id", Integer, ForeignKey("project.id"), nullable=False)
    taskKeywords = relationship("TaskKeyword", cascade="all", backref="task", cascade_backrefs=False)
    lock = relationship("TaskLock", cascade="all", backref="task", cascade_backrefs=False)

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
        Returns all keywords keys as a string like "@key1 @key2 @key3...".
        Internal keywords (starting with _) are ignored.
        """
        keywords = [k for k in list(self.getKeywordDict().keys()) if not k.startswith("_")]
        keywords.sort()
        if keywords:
            return " ".join(f"@{k}" for k in keywords)
        else:
            return ""

    def setStatus(self, status):
        """
        Defines the status of the task, taking care of updating the done date
        and doing the right thing for recurrent tasks
        """
        if self.recurrence and status == "done":
            self.dueDate = self.recurrence.getNext(self.dueDate)
        else:
            self.status = status
            if status == "done":
                self.doneDate = datetime.now().replace(second=0, microsecond=0)
            else:
                self.doneDate = None

    def setRecurrenceRule(self, rule):
        """Set recurrence and update the due date accordingly"""
        self.recurrence = rule
        self.dueDate = rule.getNext()

    @staticmethod
    def getNoteKeyword(session):
        return session.query(Keyword).filter_by(name=NOTE_KEYWORD).one()

    def toNote(self, session):
        session.add(TaskKeyword(task=self, keyword=Task.getNoteKeyword(session), value=None))
        try:
            session.flush()
        except IntegrityError:
            # Already a note
            session.rollback()
            return

    def toTask(self, session):
        noteKeyword = Task.getNoteKeyword(session)
        try:
            taskKeyword = session.query(TaskKeyword).filter_by(task=self, keyword=noteKeyword).one()
        except NoResultFound:
            # Already a task
            return
        session.delete(taskKeyword)

    def isNote(self, session):
        noteKeyword = Task.getNoteKeyword(session)
        return any((x.keyword == noteKeyword for x in self.taskKeywords))

    def __repr__(self):
        return "<Task id={} title={}>".format(self.id, self.title)


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
    taskId = Column("task_id", Integer, ForeignKey("task.id"), unique=True, nullable=False)
    pid = Column(Integer, default=None)
    updateDate = Column("update_date", DateTime, default=None)


class Alias(Base):
    __tablename__ = "alias"
    uuid = Column(Unicode, unique=True, default=uuidGenerator, nullable=False, primary_key=True)
    name = Column(Unicode, unique=True, nullable=False)
    command = Column(Unicode, nullable=False)

    @staticmethod
    def getAsDict(session):
        dct = {}
        for alias in session.query(Alias).all():
            dct[alias.name] = alias.command
        return dct

    @staticmethod
    def add(session, name, command):
        alias = Alias(name=name, command=command)
        session.add(alias)

    @staticmethod
    def rename(session, name, newName):
        alias = session.query(Alias).filter_by(name=name).one()
        alias.name = newName

    @staticmethod
    def setCommand(session, name, command):
        alias = session.query(Alias).filter_by(name=name).one()
        alias.command = command


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

        if memoryDatabase:
            connectionString = "sqlite:///:memory:"
        else:
            connectionString = 'sqlite:///' + dbFileName

        echo = os.environ.get("YOKADI_SQL_DEBUG", "0") != "0"
        self.engine = create_engine(connectionString, echo=echo)
        self.session = scoped_session(sessionmaker(bind=self.engine))

        if not os.path.exists(dbFileName) or memoryDatabase:
            if not createIfNeeded:
                raise DbUserException("Database file (%s) does not exist or is not readable." % dbFileName)
            if not memoryDatabase:
                print("Creating %s" % dbFileName)
            self.createTables()
            # Set database version according to current yokadi release
            # Don't do it in updateMode: the update script adds the version from the dump
            if not updateMode:
                self.session.add(Config(name=DB_VERSION_KEY, value=str(DB_VERSION), system=True,
                                        desc="Database schema release number"))
            self.session.commit()

        if not updateMode:
            self.checkVersion()

    def createTables(self):
        """Create all defined tables"""
        Base.metadata.create_all(self.engine)

    def getVersion(self):
        if not self._hasConfigTable():
            # There was no Config table in v1
            return 1

        try:
            return int(self.session.query(Config).filter_by(name=DB_VERSION_KEY).one().value)
        except NoResultFound:
            raise YokadiException("Configuration key '%s' does not exist. This should not happen!" % DB_VERSION_KEY)

    def setVersion(self, version):
        assert self._hasConfigTable()
        instance = self.session.query(Config).filter_by(name=DB_VERSION_KEY).one()
        instance.value = str(version)
        self.session.add(instance)
        self.session.commit()

    def _hasConfigTable(self):
        inspector = inspect(self.engine)
        return inspector.has_table("config")

    def checkVersion(self):
        """Check version and exit if it is not suitable"""
        version = self.getVersion()
        if version != DB_VERSION:
            msg = "Your database version is {} but Yokadi wants version {}.\n".format(version, DB_VERSION)
            msg += "Please run Yokadi with the --update option to update your database."
            raise DbUserException(msg)


def setDefaultConfig():
    """Set default config parameter in database if they (still) do not exist"""
    defaultConfig = {
        "ALARM_DELAY_CMD":
            ('''kdialog --passivepopup "task {TITLE} ({ID}) is due for {DATE}" 180 --title "Yokadi: {PROJECT}"''',
             False, "Command executed by Yokadi Daemon when a tasks due date is reached soon (see ALARM_DELAY"),
        "ALARM_DUE_CMD":
            ('''kdialog --passivepopup "task {TITLE} ({ID}) should be done now" 1800 --title "Yokadi: {PROJECT}"''',
             False, "Command executed by Yokadi Daemon when a tasks due date is reached soon (see ALARM_DELAY"),
        "ALARM_DELAY": ("8", False, "Delay (in hours) before due date to launch the alarm (see ALARM_CMD)"),
        "ALARM_SUSPEND": ("1", False, "Delay (in hours) before an alarm trigger again"),
        "PURGE_DELAY": ("90", False, "Default delay (in days) for the t_purge command"),
    }

    session = getSession()
    for name, value in defaultConfig.items():
        if session.query(Config).filter_by(name=name).count() == 0:
            session.add(Config(name=name, value=value[0], system=value[1], desc=value[2]))
# vi: ts=4 sw=4 et
