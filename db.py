from sqlobject import *

class Project(SQLObject):
    class sqlmeta:
        defaultOrder = "name"
    name = UnicodeCol(alternateID=True, notNone=True)


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
    project = ForeignKey("Project")
    properties = RelatedJoin("Property",
        createRelatedTable=False,
        intermediateTable="task_property",
        joinColumn="task_id",
        otherColumn="property_id")

    def setPropertyDict(self, dct):
        """
        Defines properties of a task.
        Dict is of the form: propertyName => value
        """
        for taskProperty in TaskProperty.selectBy(task=self):
            taskProperty.destroySelf()

        for name, value in dct.items():
            property = Property.selectBy(name=name)[0]
            TaskProperty(task=self, property=property, value=value)

    def getPropertyDict(self):
        """
        Returns all properties of a task as a dict of the form:
        propertyName => value
        """
        dct = {}
        for property in TaskProperty.selectBy(task=self):
            dct[property.property.name] = property.value
        return dct


def createTables():
    Project.createTable()
    Property.createTable()
    Task.createTable()
    TaskProperty.createTable()
# vi: ts=4 sw=4 et
