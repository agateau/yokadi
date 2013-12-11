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

from yokadi.core.daemon import Daemon
from yokadi.ycli import tui
from yokadi.yical.yical import YokadiIcalServer

# Force default encoding to prefered encoding
reload(sys)
sys.setdefaultencoding(tui.ENCODING)


from yokadi.core.db import Config, Project, Task, connectDatabase, getConfigKey


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
    delta = timedelta(hours=float(getConfigKey("ALARM_DELAY")))
    suspend = timedelta(hours=float(getConfigKey("ALARM_SUSPEND")))
    cmdDelayTemplate = getConfigKey("ALARM_DELAY_CMD")
    cmdDueTemplate = getConfigKey("ALARM_DUE_CMD")
    # For the two following dict, task id is key, and value is (duedate, triggerdate)
    triggeredDelayTasks = {}
    triggeredDueTasks = {}
    activeTaskFilter = [Task.q.status != "done",
                      Task.q.projectID == Project.q.id,
                      Project.q.active == True]
    while event[0]:
        now = datetime.today().replace(microsecond=0)
        delayTasks = Task.select(AND(Task.q.dueDate < now + delta,
                                   Task.q.dueDate > now,
                                   *activeTaskFilter))
        dueTasks = Task.select(AND(Task.q.dueDate < now,
                                 *activeTaskFilter))
        processTasks(delayTasks, triggeredDelayTasks, cmdDelayTemplate, suspend)
        processTasks(dueTasks, triggeredDueTasks, cmdDueTemplate, suspend)
        time.sleep(DELAY)

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

def killYokadid(pidFile):
    """Kill Yokadi daemon
    @param pidFile: file where the pid of the daemon is stored
    """
    # reuse Daemon.stop() code
    daemon = Daemon(pidFile)
    daemon.stop()

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
                      help="Kill the Yokadi daemon. The daemon is found from the process ID stored in the file specified with --pid")

    parser.add_option("-f", "--foreground",
                      dest="foreground", default=False, action="store_true",
                      help="Don't fork background. Useful for debug")

    parser.add_option("--pid",
                      dest="pidFile", default="/tmp/yokadid.pid",
                      help="File in which Yokadi daemon stores its process ID")

    parser.add_option("--log",
                      dest="logFile", default="/tmp/yokadid.log",
                      help="File in which Yokadi daemon stores its log output")

    return parser.parse_args()


class YokadiDaemon(Daemon):
    def __init__(self, options):
        Daemon.__init__(self, options.pidFile, stdout=options.logFile, stderr=options.logFile)
        self.options = options

    def run(self):
        filename = self.options.filename
        if not filename:
            filename = os.path.join(os.path.expandvars("$HOME"), ".yokadi.db")
            print "Using default database (%s)" % filename

        connectDatabase(filename, createIfNeeded=False)

        # Basic tests :
        if not (Task.tableExists() and Config.tableExists()):
            print "Your database seems broken or not initialised properly. Start yokadi command line tool to do it"
            sys.exit(1)

        # Start ical http handler
        if self.options.icalserver:
            yokadiIcalServer = YokadiIcalServer(self.options.tcpPort, self.options.tcpListen)
            yokadiIcalServer.start()

        # Start the main event Loop
        try:
            while event[1] != "SIGTERM":
                eventLoop()
                event[0] = True
        except KeyboardInterrupt:
            print "\nExiting..."


def main():
    #TODO: check that yokadid is not already running for this database ? Not very harmful...
    #TODO: change unix process name to "yokadid"

    # Make the event list global to allow communication with main event loop
    global event

    (options, args) = parseOptions()

    if options.kill:
        killYokadid(options.pidFile)
        sys.exit(0)

    signal(SIGTERM, sigTermHandler)
    signal(SIGHUP, sigHupHandler)

    daemon = YokadiDaemon(options)
    if options.foreground:
        daemon.run()
    else:
        daemon.start()

if __name__ == "__main__":
    main()
