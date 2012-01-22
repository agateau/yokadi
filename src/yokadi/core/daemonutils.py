#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Yokadi daemon helpers. Used by the yokadi daemon.

@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""

import sys
import os

try:
    from syslog import openlog, syslog, LOG_USER
    SYSLOG = True
except ImportError:
    SYSLOG = False

class YokadiLog:
    """Send ouput to syslog if available, else defaulting to /tmp/yokadid.log"""
    def __init__(self):
        self.logfile = None
        if SYSLOG:
            openlog("yokadi", 0, LOG_USER)
            syslog("init")
        else:
            try:
                self.logfile = open("/tmp/yokadid-%s.log" % os.getpid(), "w+")
            except:
                self.logfile = None

    def write(self, output):
        if SYSLOG:
            if output == "\n": return
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
        print >> sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
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
        print >> sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    sys.stdout = sys.stderr = YokadiLog()
    print "Starting Yokadi daemon with pid %s" % os.getpid()
