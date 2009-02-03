#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
    Reusable script for handling Windows Service
    
    To create or start a service: 
        - Overload BaseService virtual functions
        - Create a ServiceHandler instance, give it the your overload class.
        - Call ServiceHandler start() or install()
    
    @requires: pywin32 (https://sourceforge.net/projects/pywin32/)
    @author: Marc-Antoine Gouillart
    @license: GNU GPLv3
    
    @note: made possible by a tutorial (MIT license) at http://code.activestate.com/recipes/551780/
"""

# Pywin32 imports
import win32serviceutil
import win32service
import win32event
import win32api
import servicemanager

# Python imports
import sys
from os.path import splitext, abspath


class ServiceHandler():
    def __init__( self, 
                  serviceClass,
                  serviceName,
                  longName      = None,
                  binPath       = None,
                  binArgs       = None,
                  type          = win32service.SERVICE_WIN32_OWN_PROCESS, 
                  start         = win32service.SERVICE_DEMAND_START, 
                  error         = win32service.SERVICE_ERROR_IGNORE,
                  user          = None,
                  password      = None,
                  description   = None  ):
        self.longName       = longName or serviceName
        self.serviceName    = serviceName
        self.binPath        = binPath
        self.binArgs        = binArgs
        self.type           = type
        self.start          = start
        self.error          = error
        self.user           = user
        self.password       = password
        self.description    = description
        self.serviceClass   = serviceClass
        self.serviceClassString   = splitext(abspath(sys.modules[serviceClass.__module__].__file__))[0] + "." + serviceClass.__name__
    
        self.serviceClass._svc_name_ = self.serviceName
        self.serviceClass._svc_display_name_ = self.longName
            
            
    def startService(self):
        """ Starts the service. Raises exceptions if isn't installed, or already running """
        try:
            self.serviceClass._svc_name_ = self.serviceName
            self.serviceClass._svc_display_name_ = self.longName
            win32serviceutil.StartService(self.serviceName)
            print u'Service started OK'
        except Exception, x:
            print str(x)
            raise
    
    
    def stopService(self):
        """ Stops the service """
        try:
            win32serviceutil.StopService(self.serviceName)
            print u'Service stopped OK'
        except Exception, x:
            print str(x)
            raise
    
    def startAndOrInstallServiceNoError(self):
        if not self.isServiceInstalled():
            self.install()
        else:
            print 'Service is already installed'
        if not self.isServiceRunning():
            self.startService()
        else:
            print u'Service is already running'
    
    def isServiceRunning(self):
        """ returns True if running"""
        return win32serviceutil.QueryServiceStatus(self.serviceName)[1] == 4 
    
    def isServiceInstalled(self):
        try:
            self.isServiceRunning()
            return True
        except:
            return False
    
    def install(self):
        """
            Installs the Service
        """
        try:
            win32serviceutil.InstallService(
                    pythonClassString   = self.serviceClassString,
                    serviceName         = self.serviceName,
                    displayName         = self.longName,
                    startType           = self.start,
                    errorControl        = self.error,
                    bRunInteractive     = 0, # deprecated in Vista for security reasons (session 0 isolation)
                    userName            = self.user,
                    password            = self.password,
                    description         = self.description,
                    exeName             = self.binPath,
                    exeArgs             = self.binArgs)
            
            print 'Service install OK'
        except Exception, x:
            print str(x)
            raise
    


class BaseService(win32serviceutil.ServiceFramework):    
    def __init__(self, *args):
        if self.__class__.__name__ == 'BaseService':
            raise NotImplementedError('BaseService is an abstract class and should not be instanciated as such')
         
        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.logInfo('init')
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.isRunning = False         
    
    def logInfo(self, msg):
        servicemanager.LogInfoMsg(str(msg))
    
    def logError(self, msg):
        servicemanager.LogErrorMsg(str(msg))
    
    def logWarning(self, msg):
        servicemanager.LogWarningMsg(str(msg))
        
    def sleep(self, sec):
            win32api.Sleep(sec*1000, True)
                
    def SvcDoRun(self):
        """ This function is called by Windows at service startup"""
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.logInfo('starting service %s' %self._svc_name_)
            
            # Call main loop (provided by the end user)
            self.mainLoop()
            
            # Once loop is finished, the service should not end (would be an error) but wait for an end signal
            self.logInfo('service %s is waiting for a stop event' %self._svc_name_)
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
            self.logInfo('service %s has finished' %self._svc_name_)
        except Exception, x:
            self.logError('Service %s : [exception] %s' %(self._svc_name_, x))
            self.SvcStop()
            raise
            
            
    def SvcStop(self):
        """This function is called by Windows at service shutdown"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.logInfo('stopping')
        self.stopHook()
        self.logInfo('stopped')
        win32event.SetEvent(self.stop_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def mainLoop(self):
        raise NotImplementedError(u'A Service must implement a mainLoop function')
    
    def stopHook(self):
        raise NotImplementedError(u'A Service must implement a stopHook function')

    
    



