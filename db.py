from sqlobject import *

class Property(SQLObject):
    class sqlmeta:
        defaultOrder = "name"
    name = UnicodeCol(alternateID=True, notNone=True)
    tasks = RelatedJoin("Task",
        createRelatedTable=False,
        intermediateTable="task_property",
        joinColumn="property_id",
        otherColumn="task_id")

class TaskProperty(SQLObject):
    task = ForeignKey("Task")
    property = ForeignKey("Property")
    value = IntCol(default=None)

class Task(SQLObject):
    title = UnicodeCol(alternateID=True)
    creationDate = DateTimeCol(notNone=True)
    description = UnicodeCol(default="", notNone=True)
    urgency = IntCol(default=0, notNone=True)
    status = EnumCol(enumValues=['new', 'started', 'done'])
    properties = RelatedJoin("Property",
        createRelatedTable=False,
        intermediateTable="task_property",
        joinColumn="task_id",
        otherColumn="property_id")

    def getPropertyDict(self):
        dct = {}
        for property in TaskProperty.selectBy(task=self):
            dct[property.property.name] = property.value
        return dct


def createTables():
    Property.createTable()
    Task.createTable()
    TaskProperty.createTable()
# vi: ts=4 sw=4 et
