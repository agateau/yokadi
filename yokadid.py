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

from db import Task
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
    delta=timedelta(hours=8)
    triggeredTasks={}
    while True:
        time.sleep(DELAY)
        now=datetime.today().replace(microsecond=0)
        tasks=Task.select(AND(Task.q.dueDate < now+delta, Task.q.dueDate > now))
        for task in tasks:
            if triggeredTasks.has_key(task.id):
                if triggeredTasks[task.id]==task.dueDate:
                    # This task with the same dueDate has already been triggered, skipping
                    continue
            print "Task %s is due soon" % task.title
            #TODO: launch action for this due task
            triggeredTasks[task.id]=task.dueDate
            

def connectDatabase():
    #Use a configuration file or parsing args
    dbFileName="/home/fox/travail/yokadi.db"
    connectionString = 'sqlite:' + dbFileName
    connection = connectionForURI(connectionString)
    sqlhub.processConnection = connection

    
def main():
    #TODO: parse options
    # -f for foreground processing nofork
    # -d for time delta before warning
    # -x for command to execute when a task is due
    # argv[0] for databasename
    
    doubleFork()
    signal(SIGTERM, sigTermHandler)
    connectDatabase()
    eventLoop()

if __name__ == "__main__":
    main()