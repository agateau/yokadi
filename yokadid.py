#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Yokadi daemon. Used to monitor due tasks and warn user.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPLv3
"""

import sys, os, time
from datetime import datetime, timedelta
from signal import SIGTERM, signal
from sqlobject import AND, connectionForURI, sqlhub
from subprocess import Popen
from optparse import OptionParser
from os.path import abspath

from db import Config, Task, connectDatabase

try:
    from syslog import openlog, syslog, LOG_USER
    SYSLOG=True
except ImportError:
    SYSLOG=False

# Daemon polling delay (in seconds)
DELAY=5
    
class Log:
    """Send ouput to syslog if available, else defaulting to /tmp/yokadid.log"""
    def __init__(self):
        self.logfile=None
        if SYSLOG:
            openlog("yokadi", 0, LOG_USER)
            syslog("init")
        else:
            try:
                self.logfile=open("/tmp/yokadid-%s.log" % os.getpid(), "w+")
            except:
                self.logfile=None

    def write(self, output):
        if SYSLOG:
            if output=="\n": return
            syslog(output)
        elif self.logfile:
            self.logfile.write(output)
        else:
            sys.stdout(output)
            sys.stdout.flush()

def doubleFork():
    # Python unix daemon trick from the Activestate recipe 66012
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/")   #don't prevent unmounting
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print eventual PID before
            print "Forking background with PID %d" % pid
            sys.stdout.flush()
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)
    
    sys.stdout = sys.stderr = Log()
    print "Starting Yokadi daemon with pid %s" % os.getpid()

def sigTermHandler(signal, stack):
    """Handler when yokadid receive SIGTERM"""
    print "Receive SIGTERM. Exiting"
    print "End of yokadi Daemon"
    sys.exit(0)

def eventLoop():
    delta=timedelta(hours=int(Config.byName("ALARM_DELAY").value))
    cmdTemplate=Config.byName("ALARM_CMD").value
    #TODO: handle sighup to reload config
    triggeredTasks={}
    while True:
        time.sleep(DELAY)
        now=datetime.today().replace(microsecond=0)
        tasks=Task.select(AND(Task.q.dueDate < now+delta, Task.q.dueDate > now))
        for task in tasks:
            if triggeredTasks.has_key(task.id) and triggeredTasks[task.id]==task.dueDate:
                # This task with the same dueDate has already been triggered, skipping
                continue
            print "Task %s is due soon" % task.title
            cmd=cmdTemplate.replace("{ID}", str(task.id))
            cmd=cmd.replace("{TITLE}", task.title)
            cmd=cmd.replace("{DATE}", str(task.dueDate))
            process=Popen(cmd, shell=True)
            #TODO: redirect stdout/stderr properly to Log (not so easy...)
            triggeredTasks[task.id]=task.dueDate
            

def parseOptions():
    parser = OptionParser()
    
    parser.add_option("-d", "--db", dest="filename",
                      help="TODO database", metavar="FILE")

    parser.add_option("-k", "--kill",
                      dest="kill", default=False, action="store_true", 
                      help="Kill Yokadi Daemon (you can specify database with -db if you run multiple Yokadid")

    parser.add_option("-f", "--foreground",
                      dest="foreground", default=False, action="store_true", 
                      help="Don't fork background. Usefull for debug")

    return parser.parse_args()


def main():
    #TODO: check that yokadid is not already running for this database
    #TODO: change unix process name to "yokadid"

    (options, args) = parseOptions()

    if not options.foreground:
        doubleFork()

    signal(SIGTERM, sigTermHandler)

    if options.kill:
        print "Not yet implemented. Use kill <pid> to exit properly Yokadid"
        sys.exit(0)

    if options.filename:
        connectDatabase(options.filename, createIfNeeded=False)
        # Basic tests :
        if not (Task.tableExists() and Config.tableExists()):
            print "Your database seems broken or not initialised properly. Start yokadi command line tool to do it"
            sys.exit(1)
    else:
        print "No database given, exiting"
        sys.exit(1)

    # Start the main event Loop
    try:
        eventLoop()
    except KeyboardInterrupt:
        print "\nExiting..."

if __name__ == "__main__":
    main()
