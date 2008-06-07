from sqlobject import *

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

class Task(SQLObject):
    title = UnicodeCol(alternateID=True)
    creationDate = DateTimeCol(notNone=True)
    description = UnicodeCol(default="", notNone=True)
    urgency = IntCol(default=0, notNone=True)
    status = EnumCol(enumValues=['new', 'started', 'done'])
    keywords = RelatedJoin("Keyword",
        createRelatedTable=False,
        intermediateTable="task_keyword",
        joinColumn="task_id",
        otherColumn="keyword_id")

    def getKeywordDict(self):
        dct = {}
        for property in TaskKeyword.selectBy(task=self):
            dct[property.keyword.name] = property.value
        return dct


def createTables():
    Keyword.createTable()
    Task.createTable()
    TaskKeyword.createTable()
# vi: ts=4 sw=4 et
