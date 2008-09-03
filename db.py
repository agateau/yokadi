# -*- coding: UTF-8 -*-
"""
Database access layer using sqlobject

@author: Aurélien Gâteau <aurelien@.gateau@free.fr>
@license: GPLv3
"""

from sqlobject import BoolCol, DateTimeCol, EnumCol, ForeignKey, IntCol, RelatedJoin, SQLObject, UnicodeCol

class Project(SQLObject):
    class sqlmeta:
        defaultOrder = "name"
    name = UnicodeCol(alternateID=True, notNone=True)


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

class Config(SQLObject):
    """yokadi config"""
    class sqlmeta:
        defaultOrder = "name"
    name  = UnicodeCol(alternateID=True, notNone=True)
    value = UnicodeCol()
    system = BoolCol(default=False)

def createTables():
    Project.createTable()
    Keyword.createTable()
    Task.createTable()
    TaskKeyword.createTable()
    Config.createTable()
# vi: ts=4 sw=4 et
