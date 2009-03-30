#encoding: UTF-8

"""
    Windows MFC application that displays alerts in the notification area.
    This will, in time, become the equivalent of yokadid for Windows.
    
    Made possible by :
        - pyWin32 documentation on activestate.com
        - recipe n°nnnn on activestate.com
        - www.pycode.com/modules/id=2
        - MSDN
     
    All modification to the UI should follow the Windows GUI guidelines from MSDN:
    
    @note: This should always be started with pythonw and not python to avoid popping a useless console. 
        
    @author: Marc-Antoine Gouillart
    @license: GNU GPL v3
    @requires: pywin32
"""

#TODO: add an option "run on startup" (registers into the registry) 



#####################################################################
## Imports
#####################################################################

## Yokadi imports
import tui
from db import Config, Project, Task, connectDatabase

## Python imports
from optparse import OptionParser
from datetime import datetime, timedelta
from subprocess import Popen
import os
import sys

## SQLO imports
from sqlobject import AND

## PyWin32 imports
try:
    import win32gui
    import win32con
    import timer
    import servicemanager
    import win32gui_struct
except:
    print "PyWin32 must be installed in order to run Yokadi for Windows. See https://sourceforge.net/projects/pywin32/"
    sys.exit(1)



#####################################################################
## Windows classes
#####################################################################

class YokadiApplication(object):
    def __init__(self, tip = None, icon = None, db_file = None):
        self.logInfo('A WinYokadi instance is starting')
        
        ## Connect to the yokadi db
        try:
            self.db_file = db_file or os.path.normcase(os.path.expanduser("~/.yokadi.db"))
            connectDatabase(self.db_file, createIfNeeded=False)
            self.logInfo('WinYokadi is connected to the database %s' %self.db_file)
        except:
            self.logError("Yokadi couldn't connect to the following db : %s. Exiting." %self.db_file)
            sys.exit(1)
            
        ## Window data init
        self.hwnd               = None
        self.hinst              = None
        self.id                 = 0
        self.flags              = win32gui.NIF_MESSAGE | win32gui.NIF_ICON
        self.callbackmessage    = 1044 # = WM_TRAYMESSAGE, i.e. WM_USER + 20
        self.icon               = icon or win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        self.tip                = tip or ""
        self.info               = ""
        self.timeout            = 0
        self.infotitle          = ""
        self.infoflags          = win32gui.NIIF_NONE
        
        ## Timer data init
        self.polling_delta      = 5                                                             ## in s
        self.delta              = timedelta(hours=float(Config.byName("ALARM_DELAY").value))    ## timedeltat bewteen two analysis
        self.suspend            = timedelta(hours=float(Config.byName("ALARM_SUSPEND").value))  ## timedelta beetween two alarms for the same task
        self.cmdDelayTemplate   = Config.byName("ALARM_DELAY_CMD").value                        ## command to run to alert the user (not used here)
        self.cmdDueTemplate     = Config.byName("ALARM_DUE_CMD").value                          ## Not used either
        
        ## Payload data init
        self.triggeredDelayTasks    = {}
        self.triggeredDueTasks      = {}
        self.activeTaskFilter       = [ Task.q.status       != "done",
                                        Task.q.projectID    == Project.q.id,
                                        Project.q.active    == True ]
        
        ## Event data init
        self.message_map = {
                                win32con.WM_DESTROY: self.OnDestroy,    # window destruction
                                win32con.WM_USER + 20: self.notify,     # notification
                                win32con.WM_TIMER: self.OnTimer,        # Time events
                                win32con.WM_COMMAND: self.OnCommand     # Menu & icons events
                            }
        
        ## Menu data init
        self.menu_options = (('Quit', self.destroy),
                             ('Open Yokadi', self.startYokadiShell))
        
        ## Create window
        try:
            self.createWindow()
        except:
            self.logError("WinYokadi couldn't create its window. Exiting")
            sys.exit(1)
            
        ## Timer
        self.timer = timer.set_timer(self.polling_delta * 1000, self.OnTimer)
                
        ## Add the notification icon
        try:
            self.drawTrayIcon()
        except:
            self.logError("WinYokadi couldn't add a tray Icon")
        
        ## Start main Win Message Loop
        win32gui.PumpMessages()


    def createWindow(self):
        ## Create & register window class
        wnd_class = win32gui.WNDCLASS()
        self.hinst = wnd_class.hInstance = win32gui.GetModuleHandle(None)        ## Current main window handle
        wnd_class.lpszClassName = "WinYokadi"
        wnd_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wnd_class.lpfnWndProc = self.message_map
        
        self.wnd_class = win32gui.RegisterClass(wnd_class)
        
        ## Window style
        self.style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        
        ## Create the window
        self.hwnd = win32gui.CreateWindow(
                                              self.wnd_class,                   # Window class
                                              "meuh",                           # Title
                                              self.style,                       # style
                                              100, 100,                         # x,y
                                              200, 200,                         # w,l
                                              0,                                # parent
                                              0,                                # menu
                                              0,                                # hinstance
                                              None)                             # Must be None (context)
        ## Open the window if debug mode
        #win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)        
        
        
    def getNID(self):
        """
            Builds a NOTIFYICONDATA structure containg instance data. (This C structure is not
            fully declared in pywin32, so it has to be built manually)
        """
        nid = (
               self.hwnd,               ## Parent window handle that the icon will refer to
               self.id,                 ## Notification icon ID
               self.flags,              ## Display flags (appearance customisation & present parameters)
               self.callbackmessage,    ## The ID of the event that will be sent when ths window needs to be notified 
               self.icon,               ## Icon to display
               self.tip,                ## Tip display when the mouse hovers over the icon
               self.info,               ## Text displayed in a notification
               self.timeout,            ## Notification timeout
               self.infotitle,          ## Title of a notification
               self.infoflags           ## Flags (appearance & present params) of the notification
              )
        return tuple(nid)
    
    def drawTrayIcon(self):
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, self.getNID())
    
    def displayMenu(self):
        self.menu = win32gui.CreatePopupMenu()
        for item in self.menu_options:
            item, extra = win32gui_struct.PackMENUITEMINFO(text = item[0],
                                                           hbmpItem = None,
                                                           wID = self.menu_options.index(item))
            win32gui.InsertMenuItem(self.menu, 0, 1, item)
        
        
        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(self.menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0], pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
    
    def OnCommand(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        action = self.menu_options[id][1]
        action()
    
    def OnDestroy(self, hwnd, msg, wparam, lparam):
        self.destroy() 
    
    def destroy(self):
        """
            Removes the icon from the notification area
        """
        print "Fin WinYokadi"
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self.getNID())
        self.logInfo('WinYokadi is about to stop (%s)' %self.db_file)
        win32gui.PostQuitMessage(0)
   
    def redraw(self):
       win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self.getNID())
       self.drawTrayIcon()
    
    def notify_bubble(self, title, text, timeout = 9, icon = win32gui.NIIF_NONE):
        """
            Displays a balloon notification
            
            @param title: title of the notification
            @param text: text content of the notification
            @param timeout: seconds the bubble will stay. 9 seconds is the MS recommendation.
            @param icon: icon that will be displayed in the bubble (alert, info, ...)
        """
        self.flags = self.flags | win32gui.NIF_INFO
        self.infotitle = title
        self.info = text
        self.timeout = timeout * 1000
        self.infoflags = icon
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, self.getNID())
    
    
    def notify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_RBUTTONUP:
            self.displayMenu()
    
    def OnTimer(self, timer_id, time):
        #print "timer event"
        self.payload()
        
    def logInfo(self, msg):
        servicemanager.LogInfoMsg(str(msg))
    
    def logError(self, msg):
        servicemanager.LogErrorMsg(str(msg))
    
    def logWarning(self, msg):
        servicemanager.LogWarningMsg(str(msg))
        
    def sleep(self, sec):
            win32api.Sleep(sec*1000, True)    


    def payload(self):
        """
            The function that actually does something useful...
            Taken from yokadid.py by Sebastien Renard
        """
        now = datetime.today().replace(microsecond=0)
        delayTasks = Task.select(AND(Task.q.dueDate < now + self.delta,
                                   Task.q.dueDate > now,
                                   *self.activeTaskFilter))
        dueTasks = Task.select(AND(Task.q.dueDate < now,
                                 *self.activeTaskFilter))
        self.processTasks(delayTasks, self.triggeredDelayTasks, self.cmdDelayTemplate, self.suspend)
        self.processTasks(dueTasks, self.triggeredDueTasks, self.cmdDueTemplate, self.suspend)
    
    
    def processTasks(self, tasks, triggeredTasks, cmdTemplate, suspend):
        """
            Process a list of tasks and trigger action if needed
            @param tasks: list of tasks
            @param triggeredTasks: dict of tasks that has been triggered. Dict can be updated
            @param cmdTemplate: command line template to execute if task trigger
            @param suspend: timedelta beetween to task trigger
        """
        now = datetime.now()
        for task in tasks:
            if triggeredTasks.has_key(task.id) and triggeredTasks[task.id][0] == task.dueDate:
                # This task with the same dueDate has already been triggered
                if (now - triggeredTasks[task.id][1]) < suspend:
                    # Task has been trigger recently, skip to next
                    continue            
            
            self.notify_bubble("Yokadi", "Task %s is due soon" % task.title, 15)
            triggeredTasks[task.id]=(task.dueDate, datetime.now())
     
    def startYokadiShell(self):
        """
            Quick and dirty way of opening a Yokadi console
        """
        path = "python " + os.path.abspath(os.path.dirname(sys.argv[0]) + 'yokadi.py')
        print "Ouverture Yokadi : %s" %path
        Popen(path)



#####################################################################
## Main
#####################################################################

def parseOptions():
    parser = OptionParser()
    
    parser.add_option("-d", "--db", dest="filename",
                      help="database file to use. If not specified, will try to use the default acount db", metavar="FILE")
    parser.add_option("-u", "--unistall",
                      dest="uninstall", default=False, action="store_true", 
                      help="Removes Yokadi from the auto startup list")
    parser.add_option("-i", "--install",
                      dest="install", default=False, action="store_true", 
                      help="Inscribes Yokadi into the auto startup list, so that it will start at login.")
    
    return parser.parse_args()

def main():
    ## Parse command line
    (options, args) = parseOptions()
    
    ## Create the Windows MFC application
    appli = YokadiApplication(db_file = options.filename)
    
    ## The appli will return when it is closed


if __name__ == "__main__":
    main()