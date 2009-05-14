# -*- coding: UTF-8 -*-
"""
Database access layer using sqlobject

@author: Aurélien Gâteau <aurelien@.gateau@free.fr>
@license: GPLv3
"""

import os
import sys
from datetime import datetime
try:
    from dateutil import rrule
except ImportError:
    print "You must install dateutils to use Yokadi"
    print "This library is used for task recurrence"
    print "Get it on Gustavo Niemeyer website"
    print "Or use 'easy_install dateutils'"
    sys.exit(1)

try:
    from sqlobject import BoolCol, connectionForURI, DatabaseIndex, DateTimeCol, EnumCol, ForeignKey, IntCol, \
         RelatedJoin, sqlhub, SQLObject, SQLObjectNotFound, UnicodeCol
except ImportError:
    print "You must install SQLObject to use Yokadi"
    print "Get it on http://www.sqlobject.org/"
    print "Or use 'easy_install sqlobject'"
    sys.exit(1)

from yokadiexception import YokadiException
import tui

# Yokadi database version needed for this code
# If database config key DB_VERSION differs from this one a database migration
# is required
DB_VERSION = 3
DB_VERSION_KEY = "DB_VERSION"


class Project(SQLObject):
    class sqlmeta:
        defaultOrder = "name"
    name = UnicodeCol(alternateID=True, notNone=True)
    active = BoolCol(default=True)
    keywords = RelatedJoin("Keyword",
        createRelatedTable=False,
        intermediateTable="project_keyword",
        joinColumn="project_id",
        otherColumn="keyword_id")

    def __unicode__(self):
        return self.name

    def setKeywordDict(self, dct):
        """
        Defines keywords of a project.
        Dict is of the form: keywordName => value
        """
        for projectKeyword in ProjectKeyword.selectBy(project=self):
            projectKeyword.destroySelf()

        for name, value in dct.items():
            keyword = Keyword.selectBy(name=name)[0]
            ProjectKeyword(project=self, keyword=keyword, value=value)

    def getKeywordDict(self):
        """
        Returns all keywords of a project as a dict of the form:
        keywordName => value
        """
        dct = {}
        for keyword in ProjectKeyword.selectBy(project=self):
            dct[keyword.keyword.name] = keyword.value
        return dct

    def getKeywordsAsString(self):
        """
        Returns all keywords as a string like "key1=value1, key2=value2..."
        """
        return ", ".join(list(("%s=%s" % k for k in self.getKeywordDict().items())))


class Keyword(SQLObject):
    class sqlmeta:
        defaultOrder = "name"
    name = UnicodeCol(alternateID=True, notNone=True)
    tasks = RelatedJoin("Task",
        createRelatedTable=False,
        intermediateTable="task_keyword",
        joinColumn="keyword_id",
        otherColumn="task_id")


class TaskKeyword(SQLObject):
    task = ForeignKey("Task")
    keyword = ForeignKey("Keyword")
    value = IntCol(default=None)


class ProjectKeyword(SQLObject):
    project = ForeignKey("Project")
    keyword = ForeignKey("Keyword")
    value = IntCol(default=None)


class Task(SQLObject):
    title = UnicodeCol()
    creationDate = DateTimeCol(notNone=True)
    dueDate = DateTimeCol(default=None)
    doneDate = DateTimeCol(default=None)
    description = UnicodeCol(default="", notNone=True)
    urgency = IntCol(default=0, notNone=True)
    status = EnumCol(enumValues=['new', 'started', 'done'])
    project = ForeignKey("Project")
    keywords = RelatedJoin("Keyword",
        createRelatedTable=False,
        intermediateTable="task_keyword",
        joinColumn="task_id",
        otherColumn="keyword_id")
    recurrence = ForeignKey("Recurrence", default=None)
    uniqTaskTitlePerProject=DatabaseIndex(title, project, unique=True)

    def setKeywordDict(self, dct):
        """
        Defines keywords of a task.
        Dict is of the form: keywordName => value
        """
        for taskKeyword in TaskKeyword.selectBy(task=self):
            taskKeyword.destroySelf()

        for name, value in dct.items():
            keyword = Keyword.selectBy(name=name)[0]
            TaskKeyword(task=self, keyword=keyword, value=value)

    def getKeywordDict(self):
        """
        Returns all keywords of a task as a dict of the form:
        keywordName => value
        """
        dct = {}
        for keyword in TaskKeyword.selectBy(task=self):
            dct[keyword.keyword.name] = keyword.value
        return dct

    def getKeywordsAsString(self):
        """
        Returns all keywords as a string like "key1=value1, key2=value2..."
        """
        return ", ".join(list(("%s=%s" % k for k in self.getKeywordDict().items())))

class Recurrence(SQLObject):
    """Task reccurrence definition"""

    # Keywords used to define rrule object
    RRULES_KEYWORDS=("wkst", "count", "until", "bysetpos", "bymonth", "bymonthday",
                 "byyearday", "byweekno", "byweekday", "byhour", "byminute", "bysecond",
                 "byeaster")

    frequency = IntCol(default=rrule.DAILY, notNone=True)
    start_date = DateTimeCol(default=None)
    params = UnicodeCol(default="", notNone=True)

    def get_rrule(self):
        """Create rrule object from its Recurrence representation
        @return: dateutil.rrule.rrule instance"""
        parDict = {}
        try:
            if self.params:
                parDict = eval(self.params)
        except Exception, e:
            print "Bad recurrence parameter: %s" % e
            #TODO: should we log an exception or break upstream ?
            # Bad data here means set_params is buggy or was not used to insert data
        parDict["cache"] = True # Allow rrule cache to optimise multiple access to same rrule
        parDict["dtstart"] = self.start_date
        return rrule.rrule(self.frequency, **parDict)

    def set_rrule(self, rule):
        """Set Recurrence according to rule
        @type rule: dateutil.rrule.rrule instance"""
        if not isinstance(rule, rrule.rrule):
            raise Exception("A dateutil.rrule.rrule object if requiered")
        self.frequency = rule._freq
        self.start_date = rule._dtstart
        parDict = {}
        for key in self.RRULES_KEYWORDS:
            parDict[key] = getattr(rule, "_"+key)
        self.params = repr(parDict) # Use str representation of the dict


    def get_next(self, refDate=None):
        """Return next date of recurrence after given date
        @param refDate: reference date used to compute the next occurence of recurrence
        @type refDate: datetime
        @return: next occurence (datetime)"""
        rr = self.get_rrule()
        if refDate is None:
            refDate = datetime.now()
        return rr.after(refDate)

class Config(SQLObject):
    """yokadi config"""
    class sqlmeta:
        defaultOrder = "name"
    name  = UnicodeCol(alternateID=True, notNone=True)
    value = UnicodeCol(default="", notNone=True)
    system = BoolCol(default=False, notNone=True)
    desc = UnicodeCol(default="", notNone=True)


TABLE_LIST = [Project, Keyword, Task, TaskKeyword, ProjectKeyword, Config, Recurrence]

def createTables():
    for table in TABLE_LIST:
        table.createTable()


def getVersion():
    if not Config.tableExists():
        # There was no Config table in v1
        return 1

    try:
        return int(Config.byName(DB_VERSION_KEY).value)
    except SQLObjectNotFound:
        raise YokadiException("Configuration key '%s' does not exist. This should not happen!" % DB_VERSION_KEY)


def connectDatabase(dbFileName, createIfNeeded=True):
    """Connect to database and create it if needed
    @param dbFileName: path to database file
    @type dbFileName: str
    @param createIfNeeded: Indicate if database must be created if it does not exists (default True)
    @type createIfNeeded: bool"""

    dbFileName=os.path.abspath(dbFileName)

    if sys.platform == 'win32':
        connectionString = 'sqlite:/'+ dbFileName[0] +'|' + dbFileName[2:]
    else:
        connectionString = 'sqlite:' + dbFileName
        
    connection = connectionForURI(connectionString)
    sqlhub.processConnection = connection

    if not os.path.exists(dbFileName):
        if createIfNeeded:
            print "Creating database"
            createTables()
            # Set database version according to current yokadi release
            Config(name=DB_VERSION_KEY, value=str(DB_VERSION), system=True, desc="Database schema release number")
        else:
            print "Database file (%s) does not exist or is not readable. Exiting" % dbFileName
            sys.exit(1)

    # Check version
    version = getVersion()
    if version != DB_VERSION:
        tui.error("Your database version is %d but Yokadi wants version %d." \
            % (version, DB_VERSION))
        print "Please, run the update.py script to migrate your database prior to running Yokadi"
        sys.exit(1)

def setDefaultConfig():
    """Set default config parameter in database if they (still) do not exist"""
    defaultConfig={
        "TEXT_WIDTH"      : ("60", False, "Width of task display output with t_list command"),
        "DEFAULT_PROJECT" : ("default", False, "Default project used when no project name given"),
        "ALARM_DELAY_CMD" : ('''kdialog --passivepopup "task {TITLE} ({ID}) is due for {DATE}" 180 --title "Yokadi Daemon"''',False,
                             "Command executed by Yokadi Daemon when a tasks due date is reached soon (see ALARM_DELAY"),
        "ALARM_DUE_CMD"   : ('''kdialog --passivepopup "task {TITLE} ({ID}) should be done now" 1800 --title "Yokadi Daemon"''',False,
                             "Command executed by Yokadi Daemon when a tasks due date is reached soon (see ALARM_DELAY"),
        "ALARM_DELAY"     : ("8", False, "Delay (in hours) before due date to launch the alarm (see ALARM_CMD)"),
        "ALARM_SUSPEND"   : ("1", False, "Delay (in hours) before an alarm trigger again"),
        "PURGE_DELAY"     : ("90", False, "Default delay (in days) for the t_purge command")}

    for name, value in defaultConfig.items():
        if Config.select(Config.q.name==name).count()==0:
            Config(name=name, value=value[0], system=value[1], desc=value[2])

# vi: ts=4 sw=4 et
