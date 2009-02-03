#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
    Yokadi Service. Used to monitor due tasks and warn user.
    
    @author: Marc-Antoine Gouillart
    @license: GNU GPLv3
"""

# Yokadi imports
from winservicewrapper import BaseService, ServiceHandler
import tui
from db import Config, Project, Task, connectDatabase

# Python imports
from optparse import OptionParser
from datetime import datetime, timedelta
import os

# SQLO imports
from sqlobject import AND

# PyWin32 imports
from win32ts import WTSSendMessage, WTSEnumerateSessions, WTS_CURRENT_SERVER_HANDLE
from win32con import MB_ICONEXCLAMATION, MB_OK


###############################################################################
## Constant parameters
###############################################################################

# Daemon polling delay (in seconds)
DELAY=5



###############################################################################
## Service classes
###############################################################################

class YokadiService(BaseService):
    def stopHook(self):
        self.isRunning = False
        
    def mainLoop(self):
        """Main event loop"""
        # Some inits
        connectDatabase(self.__class__.filename, createIfNeeded=False)
        self.logInfo("Using database file %s" %self.__class__.filename)
        
        delta=timedelta(hours=int(Config.byName("ALARM_DELAY").value))
        cmdDelayTemplate=Config.byName("ALARM_DELAY_CMD").value
        cmdDueTemplate=Config.byName("ALARM_DUE_CMD").value
        triggeredDelayTasks={}
        triggeredDueTasks={}
        activeTaskFilter=[Task.q.status!="done",
                          Task.q.projectID == Project.q.id,
                          Project.q.active == True]
        
        # get user session
        for dico in WTSEnumerateSessions():
            if dico['WinStationName'] == u'Console' and dico['State'] == 0:
                sessionID = dico['SessionId']
        if not sessionID:
            raise Exception('Impossible to find the current session ID')
        self.logInfo("Using session %s for output" %sessionID)
        
        
        # Main loop itself
        self.isRunning = True
        while self.isRunning:
            self.sleep(DELAY)
            now=datetime.today().replace(microsecond=0)
            delayTasks=Task.select(AND(Task.q.dueDate < now+delta,
                                       Task.q.dueDate > now,
                                       *activeTaskFilter))
            dueTasks=Task.select(AND(Task.q.dueDate < now,
                                     *activeTaskFilter))
            self.processTasks(delayTasks, triggeredDelayTasks, cmdDelayTemplate, sessionID)
            self.processTasks(dueTasks, triggeredDueTasks, cmdDueTemplate, sessionID)


    def processTasks(self, tasks, triggeredTasks, cmdTemplate, sessionID):
        for task in tasks:
            if triggeredTasks.has_key(task.id) and triggeredTasks[task.id]==task.dueDate:
                # This task with the same dueDate has already been triggered, skipping
                continue
   
            cmd = "Task %s (%s) should be done now : it is due for the %s" %(task.title, task.id, task.dueDate)
            
            # Display a warning
            WTSSendMessage(WTS_CURRENT_SERVER_HANDLE, sessionID, 'Yokadi alert', cmd, MB_ICONEXCLAMATION + MB_OK, 999, False)
            
            # Remember that we have displayed this 
            triggeredTasks[task.id]=task.dueDate



###############################################################################
## User wish analyse
###############################################################################

def parseOptions():
    parser = OptionParser()
    
    parser.add_option("-d", "--db", dest="filename",
                      help="database file to use", metavar="FILE")

    parser.add_option("-s", "--stop",
                      dest="stop", default=False, action="store_true", 
                      help="Stops the Yokadi Service (you can specify database with -db if you run multiple YokadiS")

    parser.add_option("-u", "--unistall",
                      dest="uninstall", default=False, action="store_true", 
                      help="Removes the Yokadi Service (you can specify database with -db if you run multiple YokadiS")
    

    return parser.parse_args()


def main(start = True):
    # Parse command line
    (options, args) = parseOptions()
    
    # Open database
    if not options.filename:
        options.filename=os.path.normcase(os.path.expanduser("~/.yokadi.db"))
        print "Using default database (%s)" % options.filename
    
    print YokadiService
    YokadiService.filename = options.filename
    
    # Start service    
    sh = ServiceHandler(YokadiService, "Yokadi3", "Yokadi3 task manager Service", binArgs="-d %s" %options.filename)
    if start:
        sh.startAndOrInstallServiceNoError()

    
if __name__ == "__main__":
    main()
else:
    main(False)
    

