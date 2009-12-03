# -*- coding: UTF-8 -*-
"""
Yokadi iCalendar interface

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import os
import sys
import icalendar

import tui
# Force default encoding to prefered encoding
reload(sys)
sys.setdefaultencoding(tui.ENCODING)


from db import Config, Project, Task, connectDatabase

#TODO: code to be shared with yokadid

def generateCal():
    cal = icalendar.Calendar()
    cal.add("prodid", '-//Yokadi calendar //yokadi.github.com//')
    cal.add("version", "1.0")
    taskList = Task.select()
    for task in taskList:
        todo = icalendar.Todo()
        todo["uid"] = task.id
        todo.add("dtstamp", task.creationDate)
        todo.add("priority", task.urgency)
        todo.add("summary", task.title)
        todo.add("dtstart", task.creationDate)
        if task.dueDate:
            todo.add("due", task.dueDate)
        if task.description:
            todo.add("description", task.description)
        if task.keywords:
            todo.add("categories", [k.name for k in task.keywords])
        cal.add_component(todo)

    return cal

def main():

    filename = os.path.join(os.path.expandvars("$HOME"), ".yokadi.db")
    print "Using default database (%s)" % filename

    connectDatabase(filename, createIfNeeded=False)

    cal = generateCal()

    f = open("/tmp/yokadi.ics", "wb")
    f.write(cal.as_string())
    f.close()


    print "Exiting"

if __name__ == "__main__":
    main()
