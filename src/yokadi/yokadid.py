#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Yokadi daemon. Used to monitor due tasks and warn user.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""

import sys
import os
import time
from datetime import datetime, timedelta
from signal import SIGTERM, SIGHUP, signal
from subprocess import Popen
from optparse import OptionParser
from commands import getoutput

from sqlobject import AND

from yokadi.core.daemonutils import doubleFork
from yokadi.ycli import tui
from yokadi.yical.yical import YokadiIcalServer

# Force default encoding to prefered encoding
reload(sys)
sys.setdefaultencoding(tui.ENCODING)


from yokadi.core.db import Config, Project, Task, connectDatabase


# Daemon polling delay (in seconds)
DELAY = 30

# Ical daemon default port
DEFAULT_TCP_ICAL_PORT = 8000

# Event sender to main loop
event = [True, ""]


def sigTermHandler(signal, stack):
    """Handler when yokadid receive SIGTERM"""
    print "Receive SIGTERM. Exiting"
    print "End of yokadi Daemon"
    event[0] = False
    event[1] = "SIGTERM"

def sigHupHandler(signal, stack):
    """Handler when yokadid receive SIGHUP"""
    print "Receive SIGHUP. Reloading configuration"
    event[0] = False
    event[1] = "SIGHUP"


def eventLoop():
    """Main event loop"""
    delta = timedelta(hours=float(Config.byName("ALARM_DELAY").value))
    suspend = timedelta(hours=float(Config.byName("ALARM_SUSPEND").value))
    cmdDelayTemplate = Config.byName("ALARM_DELAY_CMD").value
    cmdDueTemplate = Config.byName("ALARM_DUE_CMD").value
    # For the two following dict, task id is key, and value is (duedate, triggerdate)
    triggeredDelayTasks = {}
    triggeredDueTasks = {}
    activeTaskFilter = [Task.q.status != "done",
                      Task.q.projectID == Project.q.id,
                      Project.q.active == True]
    while event[0]:
        time.sleep(DELAY)
        now = datetime.today().replace(microsecond=0)
        delayTasks = Task.select(AND(Task.q.dueDate < now + delta,
                                   Task.q.dueDate > now,
                                   *activeTaskFilter))
        dueTasks = Task.select(AND(Task.q.dueDate < now,
                                 *activeTaskFilter))
        processTasks(delayTasks, triggeredDelayTasks, cmdDelayTemplate, suspend)
        processTasks(dueTasks, triggeredDueTasks, cmdDueTemplate, suspend)

def processTasks(tasks, triggeredTasks, cmdTemplate, suspend):
    """Process a list of tasks and trigger action if needed
    @param tasks: list of tasks
    @param triggeredTasks: dict of tasks that has been triggered. Dict can be updated
    @param cmdTemplate: command line template to execute if task trigger
    @param suspend: timedelta beetween to task trigger"""
    now = datetime.now()
    for task in tasks:
        if triggeredTasks.has_key(task.id) and triggeredTasks[task.id][0] == task.dueDate:
            # This task with the same dueDate has already been triggered
            if now - triggeredTasks[task.id][1] < suspend:
                # Task has been trigger recently, skip to next
                continue
        print "Task %s is due soon" % task.title
        cmd = cmdTemplate.replace("{ID}", str(task.id))
        cmd = cmd.replace("{TITLE}", task.title.replace('"', '\"'))
        cmd = cmd.replace("{PROJECT}", task.project.name.replace('"', '\"'))
        cmd = cmd.replace("{DATE}", str(task.dueDate))
        process = Popen(cmd, shell=True)
        process.wait()
        #TODO: redirect stdout/stderr properly to Log (not so easy...)
        triggeredTasks[task.id] = (task.dueDate, datetime.now())

def killYokadid(dbName):
    """Kill Yokadi daemon
    @param dbName: only kill Yokadid running for this database
    """
    selfpid = os.getpid()
    for line in getoutput("ps -ef|grep python | grep [y]okadid.py ").split("\n"):
        pid = int(line.split()[1])
        if pid == selfpid:
            continue
        if dbName is None:
            print "Killing Yokadid with pid %s" % pid
            os.kill(pid, SIGTERM)
        else:
            if dbName in line:
                #BUG: quite buggy. Killing foo database will also kill foobar.
                # As we can have space in database path, it is not so easy to parse line...
                print "Killing Yokadid with database %s and pid %s" % (dbName, pid)
                os.kill(pid, SIGTERM)

def parseOptions():
    parser = OptionParser()

    parser.add_option("-d", "--db", dest="filename",
                      help="TODO database", metavar="FILE")

    parser.add_option("-i", "--icalserver",
                      dest="icalserver", default=False, action="store_true",
                      help="Start the optional HTTP Ical Server")

    parser.add_option("-p", "--port",
                      dest="tcpPort", default=DEFAULT_TCP_ICAL_PORT,
                      help="TCP port of ical server (default: %s)" % DEFAULT_TCP_ICAL_PORT,
                      metavar="PORT")

    parser.add_option("-l", "--listen",
                      dest="tcpListen", default=False, action="store_true",
                      help="Listen on all interface (not only localhost) for ical server")

    parser.add_option("-k", "--kill",
                      dest="kill", default=False, action="store_true",
                      help="Kill Yokadi Daemon (you can specify database with -db if you run multiple Yokadid")

    parser.add_option("-f", "--foreground",
                      dest="foreground", default=False, action="store_true",
                      help="Don't fork background. Useful for debug")

    return parser.parse_args()


def main():
    #TODO: check that yokadid is not already running for this database ? Not very harmful...
    #TODO: change unix process name to "yokadid"

    # Make the event list global to allow communication with main event loop
    global event

    (options, args) = parseOptions()

    if options.kill:
        killYokadid(options.filename)
        sys.exit(0)

    signal(SIGTERM, sigTermHandler)
    signal(SIGHUP, sigHupHandler)


    if not options.foreground:
        doubleFork()

    if not options.filename:
        options.filename = os.path.join(os.path.expandvars("$HOME"), ".yokadi.db")
        print "Using default database (%s)" % options.filename

    connectDatabase(options.filename, createIfNeeded=False)

    # Basic tests :
    if not (Task.tableExists() and Config.tableExists()):
        print "Your database seems broken or not initialised properly. Start yokadi command line tool to do it"
        sys.exit(1)

    # Start ical http handler
    if options.icalserver:
        yokadiIcalServer = YokadiIcalServer(options.tcpPort, options.tcpListen)
        yokadiIcalServer.start()

    # Start the main event Loop
    try:
        while event[1] != "SIGTERM":
            eventLoop()
            event[0] = True
    except KeyboardInterrupt:
        print "\nExiting..."

if __name__ == "__main__":
    main()
