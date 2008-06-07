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

    def toUtf8(self):
        title = self.title[:60]
        text = u"%03d %-60s status=%s %s" % (self.id, title, self.status[0].upper(), self.creationDate)
        return text.encode("utf-8")

def createTables():
    Keyword.createTable()
    Task.createTable()
# vi: ts=4 sw=4 et
