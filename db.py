from sqlobject import *

class Project(SQLObject):
    class sqlmeta:
        defaultOrder = "name"
    name = StringCol()
    tasks = MultipleJoin('Task')

class Task(SQLObject):
    title = StringCol()
    creationDate = DateTimeCol()
    description = StringCol()
    status = EnumCol(enumValues=['new', 'started', 'done'])
    project = ForeignKey('Project')

    def toUtf8(self):
        title = unicode(self.title, "utf-8")
        text = u"%03d %-40s status=%s %s" % (self.id, title, self.status[0].upper(), self.creationDate)
        return text.encode("utf-8")

def createTables():
    Project.createTable()
    Task.createTable()
# vi: ts=4 sw=4 et
