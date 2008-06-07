from sqlobject import *

class Keyword(SQLObject):
    class sqlmeta:
        defaultOrder = "name"
    name = UnicodeCol(alternateID=True)
    tasks = RelatedJoin("Task")

class Task(SQLObject):
    title = UnicodeCol(alternateID=True)
    creationDate = DateTimeCol()
    description = UnicodeCol()
    status = EnumCol(enumValues=['new', 'started', 'done'])
    keywords = RelatedJoin("Keyword")

def createTables():
    Keyword.createTable()
    Task.createTable()
# vi: ts=4 sw=4 et
