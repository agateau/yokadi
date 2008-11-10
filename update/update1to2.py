from sqlobject import *

""" This is the v2 table """
class Config(SQLObject):
    """yokadi config"""
    class sqlmeta:
        defaultOrder = "name"
    name  = UnicodeCol(alternateID=True, notNone=True)
    value = UnicodeCol(default="", notNone=True)
    system = BoolCol(default=False, notNone=True)
    desc = UnicodeCol(default="", notNone=True)


def updateDb(fileName):
    sqlhub.processConnection = connectionForURI('sqlite:' + fileName)

    createConfigTable()
    alterProjectTable()
    alterTaskTable()


def createConfigTable():
    Config.createTable()
    rows = [
        ("DB_VERSION"      , "2"       , True  , "Database schema release number")                   , 
        ("TEXT_WIDTH"      , "60"      , False , "Width of task display output with t_list command") , 
        ("DEFAULT_PROJECT" , "default" , False , "Default project used when no project name given")  , 
        ]
    for name, value, system, desc in rows:
        Config(name=name, value=value, system=system, desc=desc)


def alterProjectTable():
    class Project(SQLObject):
        pass
    Project.addColumn(BoolCol("active", default=True), changeSchema=True)


def alterTaskTable():
    class Task(SQLObject):
        pass
    Task.addColumn(DateTimeCol("dueDate", default=None), changeSchema=True)
# vi: ts=4 sw=4 et
