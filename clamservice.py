#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Webservice --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/clam
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

import web
import shutil
import os
import codecs
import subprocess
import glob
import sys
import datetime
import random
import re
import urllib2
import getopt
import time
from copy import copy #shallow copy (use deepcopy for deep)
from functools import wraps

if __name__ == "__main__":
    sys.path.append(sys.path[0] + '/..')
    os.environ['PYTHONPATH'] = sys.path[0] + '/..'

import clam.common.status 
import clam.common.parameters
import clam.common.formats
import clam.common.digestauth
import clam.common.data
from clam.common.util import globsymlinks, setdebug, setlog, printlog, printdebug
import clam.config.defaults as settings #will be overridden by real settings later

try:
    import MySQLdb
except ImportError:
    print >>sys.stderr, "WARNING: No MySQL support available in your version of Python! Install python-mysql "

#Maybe for later: HTTPS support
#web.wsgiserver.CherryPyWSGIServer.ssl_certificate = "path/to/ssl_certificate"
#web.wsgiserver.CherryPyWSGIServer.ssl_private_key = "path/to/ssl_private_key"


VERSION = '0.7.0'

DEBUG = False
    
DATEMATCH = re.compile(r'^[\d\.\-\s:]*$')

settingsmodule = None #will be overwritten later

setlog(sys.stdout)
#Empty defaults
#SYSTEM_ID = "clam"
#SYSTEM_NAME = "CLAM: Computional Linguistics Application Mediator"
#SYSTEM_DESCRIPTION = "CLAM is a webservice wrapper around NLP tools"
#COMMAND = ""
#ROOT = "."
#PARAMETERS = []
#URL = "http://localhost:8080"
#USERS = None


def error(msg):
    if __name__ == '__main__':
        print >>sys.stderr, "ERROR: " + msg
        sys.exit(1)
    else:
        raise Exception(msg) #Raise python errors if we were not directly invoked

def warning(msg):
    print >>sys.stderr, "WARNING: " + msg




TEMPUSER = '' #temporary global variable (not very elegant and not thread-safe!) #TODO: improve?
def userdb_lookup_dict(user, realm):
    global TEMPUSER
    printdebug("Looking up user " + user)
    TEMPUSER = user
    return settings.USERS[user] #possible KeyError is captured by digest.auth itself!


def userdb_lookup_mysql(user, realm):
    printdebug("Looking up user " + user + " in MySQL")
    host,port, mysqluser,passwd, database, table = validate_users_mysql()
    db = MySQLdb.connect(host=host,user=mysqluser,passwd=passwd,db=database, charset='utf-8', use_unicode=True)
    cursor = db.cursor()
    #simple protection against mysql injection
    user = user.replace("'","") 
    user = user.replace(";","")
    sql = "SELECT user, password FROM `" + table + "` WHERE user='" + user + "' LIMIT 1"
    cursor.execute(sql)
    password = None
    while True:
        data = cursor.fetchone()
        if data:
            user, password = data            
        else:
            break
    cursor.close()
    db.close()
    if password:
        return password
    else:
        raise KeyError

    

    
def validate_users_mysql():
    if not settings.USERS_MYSQL:
        raise Exception("No USERS_MYSQL configured")    
    if 'host' in settings.USERS_MYSQL:
        host = settings.USERS_MYSQL['host']
    else:
        host = 'localhost'
    if 'port' in settings.USERS_MYSQL:
        port = int(settings.USERS_MYSQL['port'])
    else:
        port = 3306
    if not 'user' in settings.USERS_MYSQL:
        user = settings.USERS_MYSQL['user']
    else:
        raise Exception("No MySQL user defined in USERS_MYSQL")
    if 'password' in settings.USERS_MYSQL:
        password = settings.USERS_MYSQL['password']
    else:
        raise Exception("No MySQL user defined in USERS_MYSQL")            
    if 'database' in settings.USERS_MYSQL:
        database = settings.USERS_MYSQL['database']
    else:
        raise Exception("No MySQL user defined in USERS_MYSQL")     
    if 'table' in settings.USERS_MYSQL:
        table = settings.USERS_MYSQL['table']
    else:
        raise Exception("No MySQL user defined in USERS_MYSQL")   
    return host,port, user,password, database, table

#requirelogin = lambda x: x
#if settings.USERS:
#    requirelogin = clam.common.digestauth.auth(userdb_lookup, realm= settings.SYSTEM_ID)

auth = lambda x: x

#auth = clam.common.digestauth.auth(userdb_lookup, realm= settings.SYSTEM_ID)

def requirelogin(f):
    global TEMPUSER, auth
    def wrapper(*args, **kwargs):
        
        #args = list(args)
        #args.append(TEMPUSER)
        #args = tuple(args)
        printdebug("wrapper: "+ repr(f)+", user: " + TEMPUSER)        
        if settings.USERS or settings.USERS_MYSQL:
            #f = clam.common.digestauth.auth(userdb_lookup, realm=settings.SYSTEM_ID)(f)       
            return auth(f)(*args, **kwargs)
        else:
            return f(*args, **kwargs)
    return wraps(f)(wrapper)


class TestInterface(object):
    @requirelogin
    def GET(self, user = None):
        raise web.webapi.Forbidden('Test error response')
            

class CLAMService(object):
    """CLAMService is the actual service object. See the documentation for a full specification of the REST interface."""

    urls = (
        '/', 'Index',
        '/data.js', 'InterfaceData', #provides Javascript data for the web interface
        '/style.css', 'StyleData', #provides stylesheet for the web interface
        '/(?:[A-Za-z0-9_]*)/(?:input|output)/folia.xsl', 'FoLiAXSL', #provides the FoLiA XSL in every output directory without it actually existing there
        #'/t/', 'TestInterface',
        '/([A-Za-z0-9_]*)/?', 'Project',
        '/([A-Za-z0-9_]*)/upload/?', 'Uploader',
        '/([A-Za-z0-9_]*)/output/(.*)/?', 'OutputFileHandler', #(also handles viewers, convertors, metadata, and archive download
        '/([A-Za-z0-9_]*)/input/(.*)/?', 'InputFileHandler',
        #'/([A-Za-z0-9_]*)/output/([^/]*)/([^/]*)/?', 'ViewerHandler', #first viewer is always named 'view', second 'view2' etc..
    )
    


    def __init__(self, mode = 'standalone'):
        global VERSION
        printlog("Starting CLAM WebService, version " + str(VERSION) + " ...")
        if not settings.ROOT or not os.path.isdir(settings.ROOT):
            error("Specified root path " + settings.ROOT + " not found")
        elif not settings.COMMAND.split(" ")[0] or os.system("which " + settings.COMMAND.split(" ")[0] + "> /dev/null 2> /dev/null") != 0:
            error("Specified command " + settings.COMMAND.split(" ")[0] + " not found or without execute permission")
        elif not settings.PROFILES:
            error("No profiles were defined in settings module!")
        elif not settings.PARAMETERS:
            warning("No parameters defined in settings module!")
        else:      
            lastparameter = None      
            try:
                for parametergroup, parameters in settings.PARAMETERS:
                    for parameter in parameters:
                        assert isinstance(parameter, clam.common.parameters.AbstractParameter)
                        lastparameter = parameter
            except AssertionError:
                msg = "Syntax error in parameter specification."
                if lastparameter:            
                     msg += "Last part parameter: ", lastparameter.id
                error(msg)

        self.service = web.application(self.urls, globals())
        self.service.internalerror = web.debugerror
        self.mode = mode
        printlog("Server available on http://" + settings.HOST + ":" + str(settings.PORT) +'/')
        if mode == 'fastcgi':
            web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
            self.service.run()
        elif mode == 'wsgi':
            self.application = self.service.wsgifunc()
        elif mode == 'standalone' or mode == 'cherrypy' or not mode:
            #standalone mode
            self.mode = 'standalone'
            self.service.run()
        else:
            raise Exception("Unknown mode: " + mode + ", specify 'fastcgi', 'wsgi' or 'standalone'")

    @staticmethod
    def corpusindex(): 
            """Get list of pre-installed corpora"""
            corpora = []
            for f in glob.glob(settings.ROOT + "corpora/*"):
                if os.path.isdir(f):
                    corpora.append(os.path.basename(f))
            return corpora


class Index(object):
    GHOST = False
    
    @requirelogin
    def GET(self, user = None):
        """Get list of projects"""
        projects = []
        if not user: user = 'anonymous'
        for f in glob.glob(settings.ROOT + "projects/" + user + "/*"): #TODO LATER: Implement some kind of caching
            if os.path.isdir(f):
                d = datetime.datetime.fromtimestamp(os.stat(f)[8])  
                project = os.path.basename(f)
                projects.append( ( project , d.strftime("%Y-%m-%d %H:%M:%S") ) )

        errors = "no"
        errormsg = ""

        corpora = CLAMService.corpusindex()

        render = web.template.render(settings.CLAMDIR + '/templates')

        url = 'http://' + settings.HOST
        if settings.PORT != 80:
            url += ':' + str(settings.PORT)
        if settings.URLPREFIX and settings.URLPREFIX != '/':
            if settings.URLPREFIX[0] != '/':
                url += '/'
            url += settings.URLPREFIX
        if url[-1] == '/': url = url[:-1]

        web.header('Content-Type', "text/xml; charset=UTF-8")
        return render.response(VERSION, settings.SYSTEM_ID, settings.SYSTEM_NAME, settings.SYSTEM_DESCRIPTION, user, None, url, -1 ,"",[],0, errors, errormsg, settings.PARAMETERS,corpora, None,None, settings.PROFILES, None, projects, settings.WEBSERVICEGHOST if self.GHOST else False)
        


class Project(object):
    GHOST = False

    #@staticmethod
    #def users(project):
    #    path = Project.path(project)
    #    users = []
    #    if os.path.isfile(path + '.users'):
    #        f = codecs.open(path + '.users','r','utf-8')
    #        for user in f.readlines():
    #            if user.strip():
    #                users.append(user.strip())
    #        f.close()
    #    return users    

    @staticmethod
    def validate(project):
        return re.match(r'^\w+$',project, re.UNICODE)

    @staticmethod
    def path(project, user):
        """Get the path to the project (static method)"""
        if not user: user = 'anonymous'
        return settings.ROOT + "projects/" + user + '/' + project + "/"

    @staticmethod
    def create(project, user):                
        """Create project skeleton if it does not already exist (static method)"""
        if not user: user = 'anonymous'
        if not Project.validate(project):
            raise web.webapi.Forbidden('Invalid project ID')
        printdebug("Checking if " + settings.ROOT + "projects/" + user + '/' + project + " exists") 
        if not project:
            raise web.webapi.Forbidden('No project name') 
        if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project):
            printlog("Creating project '" + project + "'")
            os.mkdir(settings.ROOT + "projects/" + user)
            os.mkdir(settings.ROOT + "projects/" + user + '/' + project)
            os.mkdir(settings.ROOT + "projects/" + user + '/' + project + "/input")
            os.mkdir(settings.ROOT + "projects/" + user + '/' + project + "/output")
            #if not settings.PROJECTS_PUBLIC:
            #    f = codecs.open(settings.ROOT + "projects/" + user + '/' + project + '/.users','w','utf-8')                         
            #    f.write(user + "\n")
            #    f.close()
        else:
            #project already exists, pass silently
            pass

    @staticmethod
    #def access(project, user):
    #    """Checks whether the specified user has access to the project"""
    #    userfile = Project.path(project) + ".users"
    #    if os.path.isfile(userfile):
    #        access = False
    #        f = codecs.open(userfile,'r','utf-8')
    #        for line in f:
    #            line = line.strip()
    #            if line and user == line.strip():
    #                access = True
    #                break
    #        f.close()
    #        return access
    #    else:
    #        return True #no access file, grant access for all users

    def pid(self, project, user):
        pidfile = Project.path(project, user) + '.pid'
        if os.path.isfile(pidfile):
            f = open(pidfile,'r')
            pid = int(f.read(os.path.getsize(pidfile)))
            f.close()
            return pid
        else:
            return 0

    def running(self,project, user):
        return os.path.isfile(Project.path(project, user) + ".pid") and not os.path.isfile(Project.path(project, user) + ".done")
        
    
    def abort(self, project, user):
        if self.pid(project, user) == 0:
            return False
        printlog("Aborting process of project '" + project + "'" )
        while not os.path.exists(Project.path(project, user) + ".done"):
            printdebug("Waiting for process to die")
            time.sleep(1)
        return True

    def done(self,project,user):
        return os.path.isfile(Project.path(project, user) + ".done")

    def exitstatus(self, project, user):
        f = open(Project.path(project, user) + ".done")
        status = int(f.read(1024))
        f.close()
        return status

    def exists(self, project, user):
        """Check if the project exists"""
        if not user: user = 'anonymous'
        printdebug("Checking if project " + project + " exists for " + user)  
        return os.path.isdir(Project.path(project, user))

    def statuslog(self,project, user):
        statuslog = []
        statusfile = Project.path(project,user) + ".status"
        totalcompletion = 0
        if os.path.isfile(statusfile):
            prevmsg = None
            f = open(statusfile)
            for line in f:
                line = line.strip()
                if line:
                    message = ""
                    completion = 0
                    timestamp = ""
                    for field in line.split("\t"):
                        if field:
                            if field[-1] == '%' and field[:-1].isdigit():
                                completion = int(field[:-1])
                                if completion > 0:
                                    totalcompletion = completion
                            elif DATEMATCH.match(field):
                                if field.isdigit():     
                                      try:
                                          d = datetime.datetime.fromtimestamp(float(field))  
                                          timestamp = d.strftime("%d/%b/%Y %H:%M:%S")
                                      except:
                                          pass
                            else:
                                message += " " + field   

                    if message and (message != prevmsg):
                        #print "STATUSLOG: t=",timestamp,"c=",completion,"msg=" + message.strip()
                        statuslog.append( (message.strip(), timestamp, completion) )
                        prevmsg = message
            msg = f.read(os.path.getsize(statusfile))
            f.close()
            statuslog.reverse()
        return statuslog, totalcompletion

    def status(self, project, user):
        global DATEMATCH
        if self.running(project, user):
            statuslog, completion = self.statuslog(project, user)
            if statuslog:
                return (clam.common.status.RUNNING, statuslog[0][0],statuslog, completion)
            else:
                return (clam.common.status.RUNNING, "The system is running",  [], 0) #running
        elif self.done(project, user):
            statuslog, completion = self.statuslog(project, user)
            if statuslog:
                return (clam.common.status.DONE, statuslog[0][0],statuslog, completion)
            else:
                return (clam.common.status.DONE, "Done", statuslog, 100)
        else:
            return (clam.common.status.READY, "Accepting new input files and selection of parameters", [], 0)


    @staticmethod
    def inputindex(project, user, d = ''):
        prefix = Project.path(project, user) + 'input/'
        for f in glob.glob(prefix + d + "/*"):
            if os.path.basename(f)[0] != '.': #always skip all hidden files
                if os.path.isdir(f):
                    for result in Project.inputindex(project, user, f[len(prefix):]):
                        yield result
                else:   
                    file = clam.common.data.CLAMInputFile(Project.path(project,user), f[len(prefix):])
                    file.attachviewers(settings.PROFILES) #attaches converters as well
                    yield file


    @staticmethod
    def outputindex(project, user, d = ''):
        prefix = Project.path(project, user) + 'output/'
        for f in glob.glob(prefix + d + "/*"):
            if os.path.basename(f)[0] != '.': #always skip all hidden files
                if os.path.isdir(f):
                    for result in Project.outputindex(project, user, f[len(prefix):]):
                        yield result
                else:   
                    file = clam.common.data.CLAMOutputFile(Project.path(project,user), f[len(prefix):])
                    file.attachviewers(settings.PROFILES) #attaches converters as well
                    yield file

    @staticmethod
    def inputindexbytemplate(project, user, inputtemplate):
        """Retrieve sorted index for the specified input template"""
        index = []
        prefix = Project.path(project, user) + 'input/'
        for linkf, f in globsymlinks(prefix + '.*.INPUTTEMPLATE.' + inputtemplate.id + '.*'):
            seq = int(linkf.split('.')[-1])
            index.append( (seq,f) )
            
        #yield CLAMFile objects in proper sequence
        for seq, f in sorted(index):
            yield seq, clam.common.data.CLAMInputFile(Project.path(project, user), f[len(prefix):])
            
            
    @staticmethod
    def outputindexbytemplate(project, user, outputtemplate):
        """Retrieve sorted index for the specified input template"""
        index = []
        prefix = Project.path(project, user) + 'output/'
        for linkf, f in globsymlinks(prefix + '.*.OUTPUTTEMPLATE.' + outputtemplate.id + '.*'):
            seq = int(linkf.split('.')[-1])
            index.append( (seq,f) )
            
        #yield CLAMFile objects in proper sequence
        for seq, f in sorted(index):
            yield seq, clam.common.data.CLAMOutputFile(Project.path(project, user), f[len(prefix):])
                        


    def response(self, user, project, parameters, errormsg = "", datafile = False):
        global VERSION

        #check if there are invalid parameters:
        if not errormsg:
            errors = "no"
        else:
            errors = "yes"

        statuscode, statusmsg, statuslog, completion = self.status(project, user)
        

        
        if statuscode == clam.common.status.DONE:
            outputpaths = Project.outputindex(project, user)
            if self.exitstatus(project, user) != 0: #non-zero codes indicate errors!
                errors = "yes"
                errormsg = "An error occurred within the system. Please inspect the error log for details"
                printlog("Child process failed, exited with non zero-exit code.")
        else:
            outputpaths = []        
        if statuscode == clam.common.status.READY:
            inputpaths = Project.inputindex(project, user)
        else:
            inputpaths = []      
        
        for parametergroup, parameterlist in parameters:
            for parameter in parameterlist:
                if parameter.error:
                    errors = "yes"
                    if not errormsg: errormsg = "One or more parameters are invalid"
                    printlog("One or more parameters are invalid")
                    break

        render = web.template.render(settings.CLAMDIR + '/templates')
        
        url = 'http://' + settings.HOST
        if settings.PORT != 80:
            url += ':' + str(settings.PORT)
        if settings.URLPREFIX and settings.URLPREFIX != '/':
            if settings.URLPREFIX[0] != '/':
                url += '/'
            url += settings.URLPREFIX
        if url[-1] == '/': url = url[:-1]

        web.header('Content-Type', "text/xml; charset=UTF-8")
        return render.response(VERSION, settings.SYSTEM_ID, settings.SYSTEM_NAME, settings.SYSTEM_DESCRIPTION, user, project, url, statuscode, statusmsg, statuslog, completion, errors, errormsg, parameters,settings.INPUTSOURCES, outputpaths,inputpaths, settings.PROFILES, datafile, None , settings.WEBSERVICEGHOST if self.GHOST else False)
        
                    
    @requirelogin
    def GET(self, project, user=None):
        """Main Get method: Get project state, parameters, outputindex"""
        if not self.exists(project, user):
            raise web.webapi.NotFound("Project " + project + " was not found for user " + user) #404
        else:
            #if user and not Project.access(project, user) and not user in settings.ADMINS:
            #    raise web.webapi.Unauthorized("Access denied to project " + project + " for user " + user) #401
            return self.response(user, project, settings.PARAMETERS) #200


    @requirelogin
    def PUT(self, project, user=None):
        """Create an empty project"""
        Project.create(project, user)
        url = 'http://' + settings.HOST
        if settings.PORT != 80:
            url += ':' + str(settings.PORT)
        if settings.URLPREFIX and settings.URLPREFIX != '/':
            if settings.URLPREFIX[0] != '/':
                url += '/'
            url += settings.URLPREFIX
        if not user: user = 'anonymous'
        msg = "Project " + project + " has been created for user " + user
        raise web.webapi.Created(msg, {'Location': url + '/' + project + '/', 'Content-Type':'text/plain','Content-Length': len(msg)}) #201

    @requirelogin
    def POST(self, project, user=None):  
        global settingsmodule
        if not user: user = 'anonymous'
        Project.create(project, user)
        #if user and not Project.access(project, user):
        #    raise web.webapi.Unauthorized("Access denied to project " + project + " for user " + user) #401
                    
        #Generate arguments based on POSTed parameters
        commandlineparams = []
        postdata = web.input()

        errors, parameters, commandlineparams = clam.common.data.processparameters(postdata, settings.PARAMETERS)
                                                
        url = 'http://' + settings.HOST
        if settings.PORT != 80:
            url += ':' + str(settings.PORT)
        if settings.URLPREFIX and settings.URLPREFIX != '/':
            if settings.URLPREFIX[0] != '/':
                url += '/'
            url += settings.URLPREFIX
        if url[-1] == '/': url = url[:-1]                                        

        if not sufficientresources():            
            printlog("*** NOT ENOUGH SYSTEM RESOURCES AVAIABLE ***")
            #TODO: Use 503 instead of 500 (but 503 not implemented in web.py)
            raise web.webapi.InternalError("There are not enough system resources available to accomodate your request. Please try again later.")

        if not errors: #We don't even bother running the profiler if there are errors
            matchedprofiles = clam.common.data.profiler(settings.PROFILES, Project.path(project, user), parameters, settings.SYSTEM_ID, settings.SYSTEM_NAME, url, printdebug)

        if errors:
            #There are parameter errors, return 403 response with errors marked
            printlog("There are parameter errors, not starting.")
            raise web.webapi.Forbidden(unicode(self.response(user, project, parameters)))
        elif not matchedprofiles:
            printlog("No profiles matching, not starting.")
            raise web.webapi.Forbidden(unicode(self.response(user, project, parameters, "No profiles matching input and parameters, unable to start. Are you sure you added all necessary input files and set all necessary parameters?")))
        else:
            #write clam.xml output file
            render = web.template.render(settings.CLAMDIR + '/templates')
            f = open(Project.path(project, user) + "clam.xml",'w')
            f.write(str(self.response(user, project, parameters, "",True)))
            f.close()



            #Start project with specified parameters
            cmd = settings.COMMAND
            cmd = cmd.replace('$PARAMETERS', " ".join(commandlineparams))
            #if 'usecorpus' in postdata and postdata['usecorpus']:
            #    corpus = postdata['usecorpus'].replace('..','') #security            
            #    #use a preinstalled corpus:
            #    if os.path.exists(settings.ROOT + "corpora/" + corpus):
            #        cmd = cmd.replace('$INPUTDIRECTORY', settings.ROOT + "corpora/" + corpus + "/")
            #    else:
            #        raise web.webapi.NotFound("Corpus " + corpus + " not found")
            #else:
            cmd = cmd.replace('$INPUTDIRECTORY', Project.path(project, user) + 'input/')
            cmd = cmd.replace('$OUTPUTDIRECTORY',Project.path(project, user) + 'output/')
            cmd = cmd.replace('$STATUSFILE',Project.path(project, user) + '.status')
            cmd = cmd.replace('$DATAFILE',Project.path(project, user) + 'clam.xml')
            cmd = cmd.replace('$USERNAME',user if user else "anonymous")
            #cmd = sum([ params if x == "$PARAMETERS" else [x] for x in COMMAND ] ),[])
            #cmd = sum([ Project.path(project) + 'input/' if x == "$INPUTDIRECTORY" else [x] for x in COMMAND ] ),[])        
            #cmd = sum([ Project.path(project) + 'output/' if x == "$OUTPUTDIRECTORY" else [x] for x in COMMAND ] ),[])        
            #TODO: protect against insertion
            if settings.COMMAND.find("2>") == -1:
                cmd += " 2> " + Project.path(project, user) + "output/error.log" #add error output
            cmd = settings.CLAMDIR + '/' + settings.DISPATCHER + ' ' +  settingsmodule + ' ' + Project.path(project, user) + ' ' + cmd
            if settings.REMOTEHOST:
                if settings.REMOTEUSER:
                    cmd = "ssh -o NumberOfPasswordPrompts=0 " + settings.REMOTEUSER + "@" + settings.REMOTEHOST() + " " + cmd
                else:
                    cmd = "ssh -o NumberOfPasswordPrompts=0 " + settings.REMOTEHOST() + " " + cmd
            printlog("Starting dispatcher " +  settings.DISPATCHER + " with " + settings.COMMAND + ": " + repr(cmd) + " ..." )
            #process = subprocess.Popen(cmd,cwd=Project.path(project), shell=True)				
            process = subprocess.Popen(cmd,cwd=settings.CLAMDIR, shell=True)				
            if process:
                pid = process.pid
                printlog("Started dispatcher with pid " + str(pid) )
                f = open(Project.path(project, user) + '.pid','w') #will be handled by dispatcher!
                f.write(str(pid))
                f.close()
                raise web.webapi.Accepted(unicode(self.response(user, project, parameters))) #returns 202 - Accepted
            else:
                raise web.webapi.InternalError("Unable to launch process")

    @requirelogin
    def DELETE(self, project, user=None):
        if not user: user = 'anonymous'
        if not self.exists(project, user):
            raise web.webapi.NotFound("No such project: " + project + " for user " + user)
        statuscode, _, _, _  = self.status(project, user)
        if statuscode == clam.common.status.RUNNING:
            self.abort(project, user)   
        printlog("Deleting project '" + project + "'" )
        shutil.rmtree(Project.path(project, user))
        msg = "Deleted"
        web.header('Content-Type', 'text/plain')
        web.header('Content-Length',len(msg))
        return msg #200                

class OutputFileHandler(object):

    @requirelogin
    def GET(self, project, filename, user=None):    
        raw = filename.split('/')

        viewer = None
        requestid = None
        
        if filename.strip('/') == "":
            #this is a request for everything
            for line in self.getarchive(project, user):
                yield line
        elif len(raw) >= 2:
            #This MAY be a viewer/metadata request, check:
            if os.path.isfile(Project.path(project, user) + 'output/' +  "/".join(raw[:-1])):
                filename = "/".join(raw[:-1])
                requestid = raw[-1].lower()                        

        try:
            outputfile = clam.common.data.CLAMOutputFile(Project.path(project, user), filename)
        except:
            raise web.webapi.NotFound()
            
        if requestid:
            if requestid == 'metadata':
                if outputfile.metadata:
                    web.header('Content-Type', 'text/xml')
                    for line in outputfile.metadata.xml().split("\n"):
                        yield line                    
                else:
                    raise web.webapi.NotFound("No metadata found!")
            else:
                #attach viewer data (also attaches converters!
                outputfile.attachviewers(settings.PROFILES)
                
                viewer = None
                for v in outputfile.viewers:
                    if v.id == requestid:
                        viewer = v
                if viewer:                    
                    output = viewer.view(outputfile, **web.input())
                    if isinstance(output, web.template.TemplateResult):
                       output =  output['__body__']                  
                    for line in output:
                        yield line
                else:
                    #Check for converters
                    for c in outputfile.converters:
                        if c.id == requestid:
                            converter = c
                    if converter:
                        for line in converter.convertforoutput(outputfile):
                            yield line
                    else:
                        raise web.webapi.NotFound("No such viewer or converter:" + requestid)
        else:
            #normal request - return file contents
            if outputfile.metadata:
                for header, value in outputfile.metadata.httpheaders():
                    web.header(header, value)
            try:
                for line in outputfile:
                    yield line
            except IOError: 
                raise web.webapi.NotFound()
            except UnicodeError:
                raise web.webapi.InternalError("Output file " + str(outputfile) + " is not in the expected encoding! Make sure encodings for output templates service configuration file are accurate.")
    
    @requirelogin
    def DELETE(self, project, filename, user=None):    
        """Delete an output file"""
        
        filename = filename.replace("..","") #Simple security
        
        if len(filename) == 0:
            #Deleting all output files and resetting
            self.reset(project, user)
            msg = "Deleted"
            web.header('Content-Type', 'text/plain')
            web.header('Content-Length',len(msg))
            return msg #200
        elif os.path.isdir(Project.path(project, user) + filename): 
            #Deleting specified directory
            shutil.rmtree(Project.path(project, user) + filename)
            msg = "Deleted"
            web.header('Content-Type', 'text/plain')
            web.header('Content-Length',len(msg))
            return msg #200
        else:
            try:
                file = clam.common.data.CLAMOutputFile(Project.path(project, user), filename)
            except:
                raise web.webapi.NotFound()
                
            success = file.delete()            
            if not success:
                raise web.webapi.NotFound()
            else:
                msg = "Deleted"
                web.header('Content-Type', 'text/plain')
                web.header('Content-Length',len(msg))
                return msg #200   


    def reset(self, project, user):
        """Reset system, delete all output files and prepare for a new run"""
        d = Project.path(project, user) + "output"
        if os.path.isdir(d):
            shutil.rmtree(d)
            os.mkdir(d)
        else:
            raise web.webapi.NotFound()
        if os.path.exists(Project.path(project, user) + ".done"):
            os.unlink(Project.path(project, user) + ".done")                       
        if os.path.exists(Project.path(project, user) + ".status"):
            os.unlink(Project.path(project, user) + ".status")        

    def getarchive(self, project, user):
        """Generates and returns a download package (or 403 if one is already in the process of being prepared)"""
        if os.path.isfile(Project.path(project, user) + '.download'):
            #make sure we don't start two compression processes at the same time
            raise web.forbidden()
        else:
            data = web.input()
            if 'format' in data:
                format = data['format']
            else:
                format = 'zip' #default

            #validation, security
            contentencoding = None
            if format == 'zip':
                contenttype = 'application/zip'
                command = "/usr/bin/zip -r" #TODO: do not hard-code path!
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".tar.gz"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".tar.gz")
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".tar.bz2"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".tar.bz2")
            elif format == 'tar.gz':
                contenttype = 'application/x-tar'
                contentencoding = 'gzip'
                command = "/bin/tar -czf"
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".zip"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".zip")
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".tar.bz2"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".tar.bz2")
            elif format == 'tar.bz2': 
                contenttype = 'application/x-bzip2'
                command = "/bin/tar -cjf"
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".tar.gz"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".tar.gz")
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".zip"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".zip")
            else:
                raise web.webapi.Forbidden('Invalid archive format') #TODO: message won't show

            path = Project.path(project, user) + "output/" + project + "." + format
            
            if not os.path.isfile(path):
                printlog("Building download archive in " + format + " format")
                cmd = command + ' ' + project + '.' + format + ' *'
                printdebug(cmd)
                printdebug(Project.path(project, user)+'output/')
                process = subprocess.Popen(cmd, cwd=Project.path(project, user)+'output/', shell=True)	        			
                if not process:
                    raise web.webapi.InternalError("Unable to make download package")                
                else:
                    pid = process.pid
                    f = open(Project.path(project, user) + '.download','w') 
                    f.write(str(pid))
                    f.close()
                    os.waitpid(pid, 0) #wait for process to finish
                    os.unlink(Project.path(project, user) + '.download')

            if contentencoding:
                web.header('Content-Encoding', contentencoding)
            web.header('Content-Type', contenttype)
            for line in open(path,'r'):
                yield line
        

class InputFileHandler(object):

    @requirelogin
    def GET(self, project, filename, user=None):    
        raw = filename.split('/')

        viewer = None
        requestid = None
        
        if filename.strip('/') == "":
            #this is a request for the index
            raise web.webapi.Forbidden()
        if len(raw) >= 2:
            #This MAY be a viewer/metadata request, check:
            if os.path.isfile(Project.path(project, user) + 'input/' +  "/".join(raw[:-1])):
                filename = "/".join(raw[:-1])
                requestid = raw[-1].lower()                        

        try:
            inputfile = clam.common.data.CLAMInputFile(Project.path(project, user), filename)
        except:
            raise web.webapi.NotFound()
            
        if requestid:
            if requestid == 'metadata':
                if inputfile.metadata:
                    web.header('Content-Type', 'text/xml')
                    for line in inputfile.metadata.xml().split("\n"):
                        yield line                    
                else:
                    raise web.webapi.NotFound("No metadata found!")
            else:
                raise web.webapi.NotFound()
        else:
            #normal request - return file contents
            if inputfile.metadata:
                for header, value in inputfile.metadata.httpheaders():
                    web.header(header, value)
            try:
                for line in inputfile:
                    yield line
            except IOError: 
                raise web.webapi.NotFound()



    @requirelogin
    def DELETE(self, project, filename, user=None):    
        """Delete an input file"""
        
        filename = filename.replace("..","") #Simple security
        
        if len(filename) == 0:
            #Deleting all input files
            shutil.rmtree(Project.path(project, user) + 'input')
            os.mkdir(Project.path(project, user) + 'input') #re-add new input directory
            return "Deleted" #200
        elif os.path.isdir(Project.path(project, user) + filename): 
            #Deleting specified directory
            shutil.rmtree(Project.path(project, user) + filename)
            return "Deleted" #200
        else:
            try:
                file = clam.common.data.CLAMInputFile(Project.path(project, user), filename)
            except:
                raise web.webapi.NotFound()
                
            success = file.delete()            
            if not success:
                raise web.webapi.NotFound()
            else:
                msg = "Deleted"
                web.header('Content-Type', 'text/plain')
                web.header('Content-Length',len(msg))
                return msg #200

    @requirelogin
    def POST(self, project, filename, user=None): 
        """Add a new input file, this invokes the actual uploader"""

        #TODO: test support for uploading metadata files
        
        #TODO LATER: re-add support for archives?
        
        postdata = web.input(file={})
        
        if filename == '':
            #Handle inputsource
            if 'inputsource' in postdata and postdata['inputsource']:
                inputsource = None
                inputtemplate = None
                for s in settings.INPUTSOURCES:
                    if s.id == postdata['inputsource']:
                        inputsource = s
                if not inputsource:
                    for profile in settings.PROFILES:
                        for t in profile.input:
                            for s in t.inputsources:
                                if s.id == postdata['inputsource']:
                                    inputsource = s
                                    inputsource.inputtemplate = t.id
                                    inputtemplate = t
                                    break                    
                if not inputsource:
                    raise web.webapi.Forbidden("No such inputsource exists")
                if not inputtemplate:
                    for profile in settings.PROFILES:
                        for t in profile.input:
                            if inputsource.inputtemplate == t.id:
                                inputtemplate = t
                assert (inputtemplate != None)    
                if inputsource.isfile():
                    if inputtemplate.filename:
                        filename = inputtemplate.filename
                    else:
                        filename = os.path.basename(inputsource.path)                
                    return self.addfile(project, filename, user, {'inputsource': postdata['inputsource'], 'inputtemplate': inputtemplate.id}, inputsource)
                elif inputsource.isdir():
                    if inputtemplate.filename:
                        filename = inputtemplate.filename
                    for f in glob.glob(inputsource.path + "/*"):
                        if not inputtemplate.filename:
                            filename = os.path.basename(f)                          
                        if f[0] != '.':
                            tmpinputsource = clam.common.data.InputSource(id='tmp',label='tmp',path=f, metadata=inputsource.metadata)
                            self.addfile(project, filename, user, {'inputsource':'tmp', 'inputtemplate': inputtemplate.id}, tmpinputsource)
                            #WARNING: Output is dropped silently here!
                    return "" #200
                else:
                    assert False                    
            else:
                raise web.webapi.Forbidden("No filename or inputsource specified")
        else:
            #Simply forward to addfile
            return self.addfile(project,filename,user, postdata)
        
        
    def addfile(self, project, filename, user, postdata, inputsource=None):
        """Add a new input file, this invokes the actual uploader"""

        inputtemplate = None
        metadata = None
            
        
        if 'inputtemplate' in postdata:
            #An input template must always be provided            
            for profile in settings.PROFILES:
                for t in profile.input:
                    if t.id == postdata['inputtemplate']:
                        inputtemplate = t
            if not inputtemplate:
                #Inputtemplate not found, send 404
                printlog("Specified inputtemplate (" + postdata['inputtemplate'] + ") not found!")
                raise web.webapi.NotFound("Specified inputtemplate (" + postdata['inputtemplate'] + ") not found!")
        else:
            #Check if the specified filename can be uniquely associated with an inputtemplate
            for profile in settings.PROFILES:
                for t in profile.input:
                    if t.filename == filename:
                        if inputtemplate:
                            #we found another one, not unique!! reset and break
                            inputtemplate = None
                            break
                        else:
                            #good, we found one, don't break cause we want to make sure there is only one
                            inputtemplate = t                        
            if not inputtemplate:
                printlog("No inputtemplate specified and filename does not uniquely match with any inputtemplate!")
                raise web.webapi.NotFound("No inputtemplate specified nor auto-detected for this filename!")
                
            
            
        #See if other previously uploaded input files use this inputtemplate
        if inputtemplate.unique:
            nextseq = 0 #unique
        else:
            nextseq = 1 #will hold the next sequence number for this inputtemplate (in multi-mode only)
            
        for seq, inputfile in Project.inputindexbytemplate(project, user, inputtemplate):
            if inputtemplate.unique:
                raise web.webapi.Forbidden("You have already submitted a file of this type, you can only submit one. Delete it first. (Inputtemplate=" + inputtemplate.id + ", unique=True)") #(it will have to be explicitly deleted by the client first)
            else:
                if seq >= nextseq:
                    nextseq = seq + 1 #next available sequence number
            

        if not filename: #Actually, I don't think this can occur at this stage, but we'll leave it in to be sure
            if inputtemplate.filename:
                filename = inputtemplate.filename
            elif inputtemplate.extension: 
                filename = str(nextseq) +'-' + str("%034x" % random.getrandbits(128)) + '.' + inputtemplate.extension
            else:
                filename = str(nextseq) +'-' + str("%034x" % random.getrandbits(128)) 
                
        #Make sure filename matches (only if not an archive)
        if inputtemplate.acceptarchive and (filename[-7:].lower() == '.tar.gz' or filename[-8:].lower() == '.tar.bz2' or filename[-4:].lower() == '.zip'):                
            pass
        else:    
            if inputtemplate.filename:
                if filename != inputtemplate.filename:
                    raise web.webapi.Forbidden("Specified filename must the filename dictated by the inputtemplate, which is " + inputtemplate.filename)
                #TODO LATER: add support for calling this with an actual number instead of #
            if inputtemplate.extension:
                if filename[-len(inputtemplate.extension) - 1:].lower() == '.' + inputtemplate.extension.lower():
                    #good, extension matches (case independent). Let's just make sure the case is as defined exactly by the inputtemplate
                    filename = filename[:-len(inputtemplate.extension) - 1] +  '.' + inputtemplate.extension
                else:
                    raise web.webapi.Forbidden("Specified filename does not have the extension dictated by the inputtemplate ("+inputtemplate.extension+")") #403
            
        if inputtemplate.onlyinputsource and (not 'inputsource' in postdata or not postdata['inputsource']):
            raise web.webapi.Forbidden("Adding files for this inputtemplate must proceed through inputsource") #403
            
        if 'converter' in postdata and postdata['converter'] and not postdata['converter'] in [ x.id for x in inputtemplate.converters]:            
                raise web.webapi.Forbidden("Invalid converter specified: " + postdata['converter']) #403

        #Very simple security, prevent breaking out the input dir
        filename = filename.replace("..","")


        #Create the project (no effect if already exists)
        Project.create(project, user)        


        
        
        web.header('Content-Type', "text/xml; charset=UTF-8")
        head = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        head += "<clamupload>\n"
        
        
        
        if 'file' in postdata and (not isinstance(postdata['file'], dict) or len(postdata['file']) > 0):
            printlog("Adding client-side file " + postdata['file'].filename + " to input files")            
            sourcefile = postdata['file'].filename
        elif 'url' in postdata and postdata['url']:
            #Download from URL
            printlog("Adding web-based URL " + postdata['url'] + " to input files")
            sourcefile = postdata['url']    
        elif 'contents' in postdata and postdata['contents']:
            #In message
            printlog("Adding file " + filename + " with explicitly provided contents to input files")
            sourcefile = "editor"
        elif 'inputsource' in postdata and postdata['inputsource']:
            printlog("Adding file " + filename + " from preinstalled data to input files")
            if not inputsource:
                inputsource = None                    
                for s in inputtemplate.inputsources:
                    if s.id.lower() == postdata['inputsource'].lower():
                        inputsource = s
                if not inputsource:
                    raise web.webapi.Forbidden("Specified inputsource '" + postdata['inputsource'] + "' does not exist for inputtemplate '"+inputtemplate.id+"'")
            sourcefile = os.path.basename(inputsource.path)
        else:
            raise web.webapi.Forbidden("No file, url or contents specified!")
            


          
        #============================ Generate metadata ========================================
        printdebug('(Generating and validating metadata)')
        if ('metafile' in postdata and (not isinstance(postdata['metafile'], dict) or len(postdata['metafile']) > 0)):
            #an explicit metadata file was provided, upload it:
            printlog("Metadata explicitly provided in file, uploading...")          
            try:
                metadata = clam.common.data.CLAMMetaData.fromxml(postdata['metafile'])
                errors, parameters = inputtemplate.validate(metadata, user)
                validmeta = True
            except Exception, e:
                printlog("Uploaded metadata is invalid! " + str(e))          
                metadata = None
                errors = True
                parameters = []
                validmeta = False            
        elif 'metadata' in postdata and postdata['metadata']:
            printlog("Metadata explicitly provided in message, uploading...")
            try:
                metadata = clam.common.data.CLAMMetaData.fromxml(postdata['metadata'])
                errors, parameters = inputtemplate.validate(metadata, user)
                validmeta = True
            except:
                printlog("Uploaded metadata is invalid!")          
                metadata = None
                errors = True
                parameters = []
                validmeta = False 
        elif 'inputsource' in postdata and postdata['inputsource']:
            printlog("Getting metadata from inputsource, uploading...")
            if inputsource.metadata:
                printlog("DEBUG: Validating metadata from inputsource")
                metadata = inputsource.metadata
                errors, parameters = inputtemplate.validate(metadata, user)
                validmeta = True
            else:
                printlog("DEBUG: No metadata provided with inputsource, looking for metadata files..")
                metafilename = os.path.dirname(inputsource.path) 
                if metafilename: metafilename += '/'
                metafilename += '.' + os.path.basename(inputsource.path) + '.METADATA'            
                if os.path.exists(metafilename):
                    try:
                        metadata = clam.common.data.CLAMMetaData.fromxml(open(metafilename,'r').readlines())
                        errors, parameters = inputtemplate.validate(metadata, user)
                        validmeta = True
                    except:
                        printlog("Uploaded metadata is invalid!")          
                        metadata = None
                        errors = True
                        parameters = []
                        validmeta = False             
                else:
                     raise web.webapi.InternalError("No metadata found nor specified for inputsource " + inputsource.id )
        else:
            errors, parameters = inputtemplate.validate(postdata, user)
            validmeta = True #will be checked later


        #  ----------- Check if archive are allowed -------------
        archive = False
        addedfiles = []  
        if not errors and inputtemplate.acceptarchive:
            printdebug('(Archive test)')
            # -------- Are we an archive? If so, determine what kind
            archivetype = None
            if 'file' in postdata and (not isinstance(postdata['file'], dict) or len(postdata['file']) > 0):
                uploadname = sourcefile.lower()
                archivetype = None
                if uploadname[-4:] == '.zip':
                    archivetype = 'zip'
                elif uploadname[-7:] == '.tar.gz':
                    archivetype = 'tar.gz'
                elif uploadname[-8:] == '.tar.bz2':
                    archivetype = 'tar.bz2'
                    
                # NOT ACTUAL ARCHIVES
                #elif uploadname[-4:] == '.bz2':
                #    archivetype = 'bz2'
                #elif uploadname[-3:] == '.gz':
                #    archivetype = 'gz' 
            
            if archivetype:     
                # =============== upload archive ======================
                #random name
                archive = "%032x" % random.getrandbits(128) + '.' + archivetype
                    
                #Upload file from client to server
                printdebug('(Archive transfer starting)')
                f = open(Project.path(project,user) + archive,'wb')
                for line in postdata['file'].file:
                    f.write(line)
                f.close()
                printdebug('(Archive transfer completed)')
                # =============== Extract archive ======================
                
                #Determine extraction command
                if archivetype == 'zip':
                    cmd = 'unzip -u'
                elif archivetype == 'tar':
                    cmd = 'tar -xvf'
                elif archivetype == 'tar.gz':
                    cmd = 'tar -xvzf'
                elif archivetype == 'tar.bz2':
                    cmd = 'tar -xvjf'
                else:
                    raise Exception("Invalid archive format: " + archivetype) #invalid archive, shouldn't happend

                #invoke extractor
                printlog("Extracting '" + archive + "'" )            
                try:
                    process = subprocess.Popen(cmd + " " + archive, cwd=Project.path(project,user), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                except:
                    raise web.webapi.InternalError("Unable to extract archive")       
                out, err = process.communicate() #waits for process to end 


                #Read filename results
                              
                firstline = True
                for line in out.split("\n"):    
                    line = line.strip()        
                    if line:
                        printdebug('(Extraction output: ' + line+')')
                        subfile = None
                        if archivetype[0:3] == 'tar':
                            subfile = line
                        elif archivetype == 'zip' and not firstline: #firstline contains archive name itself, skip it
                            colon = line.find(":")
                            if colon:
                                subfile =  line[colon + 1:].strip()
                        if subfile and os.path.exists(Project.path(project, user) + subfile):
                            subfile_newname = clam.common.data.resolveinputfilename(os.path.basename(subfile), parameters, inputtemplate, nextseq+len(addedfiles), project) 
                            printdebug('(Extracted file ' + subfile + ', moving to input/' + subfile_newname+')')
                            os.rename(Project.path(project, user) + subfile, Project.path(project, user) + 'input/' +  subfile_newname)
                            addedfiles.append(subfile_newname)
                    firstline = False
                                        
                #all done, remove archive
                os.unlink(Project.path(project, user) + archive)
                
        if not archive:
            addedfiles = [clam.common.data.resolveinputfilename(filename, parameters, inputtemplate, nextseq, project)]

        fatalerror = None                
        
        
        output = head
        for filename in addedfiles:
            output += "<upload source=\""+sourcefile +"\" filename=\""+filename+"\" inputtemplate=\"" + inputtemplate.id + "\" templatelabel=\""+inputtemplate.label+"\">\n"            
                        
            if not errors:
                output += "<parameters errors=\"no\">"
            else:
                output += "<parameters errors=\"yes\">"
            for parameter in parameters:
                output += parameter.xml()
            output += "</parameters>"
            

            
            if not errors:
                if not archive:
                    #============================ Transfer file ========================================
                    printdebug('(Start file transfer: ' +  Project.path(project, user) + 'input/' + filename+' )')
                    if 'file' in postdata and (not isinstance(postdata['file'], dict) or len(postdata['file']) > 0):
                        #Upload file from client to server
                        f = open(Project.path(project, user) + 'input/' + filename,'wb')
                        for line in postdata['file'].file:
                            f.write(line) #encoding unaware, seems to solve big-file upload problem
                        f.close()
                    elif 'url' in postdata and postdata['url']:
                        #Download file from 3rd party server to CLAM server
                        try:
                            req = urllib2.urlopen(postdata['url'])
                        except:
                            raise web.webapi.NotFound()
                        CHUNK = 16 * 1024
                        f = open(Project.path(project, user) + 'input/' + filename,'wb')
                        while True:
                            chunk = req.read(CHUNK)
                            if not chunk: break
                            f.write(chunk)     
                        f.close()
                    elif 'contents' in postdata and postdata['contents']:  
                        #grab encoding
                        encoding = 'utf-8'
                        for p in parameters:
                            if p.id == 'encoding':
                                encoding = p.value                        
                        #Contents passed in POST message itself
                        try:
                            f = codecs.open(Project.path(project, user) + 'input/' + filename,'w',encoding)
                            f.write(postdata['contents'])
                            f.close()
                        except UnicodeError:
                            raise web.webapi.Forbidden("Input file " + str(filename) + " is not in the expected encoding!")
                    elif 'inputsource' in postdata and postdata['inputsource']:                
                        #Copy (symlink!) from preinstalled data
                        os.symlink(inputsource.path, Project.path(project, user) + 'input/' + filename)
                    
                    printdebug('(File transfer completed)')
                    
                
            
                #Create a file object
                file = clam.common.data.CLAMInputFile(Project.path(project, user), filename, False) #get CLAMInputFile without metadata (chicken-egg problem, this does not read the actual file contents!
                
                
                
                #============== Generate metadata ==============

                metadataerror = None
                if not metadata and not errors: #check if it has not already been set in another stage
                    #for newly generated metadata
                    try:
                        #Now we generate the actual metadata object (unsaved yet though). We pass our earlier validation results to prevent computing it again
                        validmeta, metadata, parameters = inputtemplate.generate(file, (errors, parameters ))
                        if validmeta:
                            #And we tie it to the CLAMFile object
                            file.metadata = metadata
                            #Add inputtemplate ID to metadata
                            metadata.inputtemplate = inputtemplate.id
                        else:
                            metadataerror = "Undefined error"
                    except ValueError, msg:
                        validmeta = False
                        metadataerror = msg
                    except KeyError, msg:
                        validmeta = False
                        metadataerror = msg
                elif validmeta:
                    #for explicitly uploaded metadata
                    metadata.file = file
                    file.metadata = metadata
                    metadata.inputtemplate = inputtemplate.id
                    
                if metadataerror:    
                    #output += "<metadataerror />" #This usually indicates an error in service configuration!
                    fatalerror = "<error type=\"metadataerror\">Metadata could not be generated for " + filename + ": " + metadataerror + " (this usually indicates an error in service configuration!)</error>"
                elif validmeta:                    
                    #=========== Convert the uploaded file (if requested) ==============
                    
                    conversionerror = False
                    if 'converter' in postdata and postdata['converter']:
                        for c in inputtemplate.converters:
                            if c.id == postdata['converter']:
                                converter = c
                                break
                        if converter: #(should always be found, error already provided earlier if not)
                            try:
                                success = converter.convertforinput(Project.path(project, user) + 'input/' + filename, metadata)
                            except:
                                success = False
                            if not success:
                                conversionerror = True
                                fatalerror = "<error type=\"conversion\">The file " + filename + " could not be converted</error>"
                
                    #====================== Validate the file itself ====================
                    if not conversionerror:
                        valid = file.validate()        
                        
                        if valid:                       
                            output += "<valid>yes</valid>"                
                                            
                            #Great! Everything ok, save metadata
                            metadata.save(Project.path(project, user) + 'input/' + file.metafilename())
                            
                            #And create symbolic link for inputtemplates
                            linkfilename = os.path.dirname(filename) 
                            if linkfilename: linkfilename += '/'
                            linkfilename += '.' + os.path.basename(filename) + '.INPUTTEMPLATE' + '.' + inputtemplate.id + '.' + str(nextseq)
                            os.symlink(Project.path(project, user) + 'input/' + filename, Project.path(project, user) + 'input/' + linkfilename)
                        else:
                            #Too bad, everything worked out but the file itself doesn't validate.
                            #output += "<valid>no</valid>"
                            fatalerror = "<error type=\"validation\">The file " + filename + " did not validate, it is not in the proper expected format.</error>"
                        
                            #remove upload
                            os.unlink(Project.path(project, user) + 'input/' + filename)
            
            
            output += "</upload>\n"       

        output += "</clamupload>"
        
        
        
        if fatalerror:
            #fatal error return error message with 403 code
            raise web.webapi.Forbidden(head + fatalerror)
        elif errors:
            #parameter errors, return XML output with 403 code
            raise web.webapi.Forbidden(output)
        else:
            #everything ok, return XML output with 200 code
            return output


    def extract(self,project,filename, archivetype):
        #namelist = None
        subfiles = []
        

        #return [ subfile for subfile in subfiles ] #return only the files that actually exist
        



class InterfaceData(object):
    """Provides Javascript data needed by the webinterface. Such as JSON data for the inputtemplates"""

    @requirelogin
    def GET(self, project, user=None):
        web.header('Content-Type', 'application/javascript')
        
        inputtemplates_mem = []
        inputtemplates = []
        for profile in settings.PROFILES:
            for inputtemplate in profile.input:
                if not inputtemplate in inputtemplates: #no duplicates
                    inputtemplates_mem.append(inputtemplate)
                    inputtemplates.append( inputtemplate.json() )

        url = 'http://' + settings.HOST
        if settings.PORT != 80:
            url += ':' + str(settings.PORT)
        if settings.URLPREFIX and settings.URLPREFIX != '/':
            if settings.URLPREFIX[0] != '/':
                url += '/'
            url += settings.URLPREFIX
        if url[-1] == '/': url = url[:-1]

        return "systemid = '"+ settings.SYSTEM_ID + "'; baseurl = '" + url + "';\n inputtemplates = [ " + ",".join(inputtemplates) + " ];"

class FoLiAXSL(object):
    """Provides Stylesheet"""
    def GET(self):
        web.header('Content-Type', 'text/xsl')

        for line in codecs.open(settings.CLAMDIR + '/static/folia.xsl','r','utf-8'):
            yield line

class StyleData(object):
    """Provides Stylesheet"""

    def GET(self):
        web.header('Content-Type', 'text/css')

        for line in codecs.open(settings.CLAMDIR + '/style/' + settings.STYLE + '.css','r','utf-8'):
            yield line
        
class ProjectGhost(Project):
    GHOST=True
    pass

class IndexGhost(Index):
    GHOST=True
    pass
        
#class Uploader(object): #OBSOLETE!

    #def path(self, project):
        #return Project.path(project) + 'input/'

    #def isarchive(self,filename):
        #return (filename[-3:] == '.gz' or filename[-4:] == '.bz2' or filename[-4:] == '.zip')

    #def extract(self,project,filename, format):
        #namelist = None
        #subfiles = []
        #if filename[-7:].lower() == '.tar.gz':
            #cmd = 'tar -xvzf'
            #namelist = 'tar'
        #elif filename[-7:].lower() == '.tar.bz2':
            #cmd = 'tar -xvjf'
            #namelist = 'tar'
        #elif filename[-3:].lower() == '.gz':
            #cmd = 'gunzip'
            #subfiles = [filename[-3:]]  #one subfile only
        #elif filename[-4:].lower() == '.bz2':
            #cmd = 'bunzip2'
            #subfiles = [filename[-3:]] #one subfile only
        #elif filename[-4:].lower() == '.tar':
            #cmd = 'tar -xvf'
            #namelist = 'tar'
        #elif filename[-4:].lower() == '.zip':
            #cmd = 'unzip -u'
            #namelist = 'zip'
        #else:
            #raise Exception("Invalid archive format") #invalid archive, shouldn't happend

        #printlog("Extracting '" + filename + "'" )            
        #try:
            #process = subprocess.Popen(cmd + " " + filename, cwd=self.path(project), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        #except:
            #raise web.webapi.InternalError("Unable to extract file: " + cmd + " " + filename + ", cwd="+ self.path(project))       
        #out, err = process.communicate() #waits for process to end 

        #if namelist:
            #firstline = True
            #for line in out.split("\n"):    
                #line = line.strip()        
                #if line:
                    #subfile = None
                    #if namelist == 'tar':
                        #subfile = line
                    #elif namelist == 'zip' and not firstline: #firstline contains archive name itself, skip it
                        #colon = line.find(":")
                        #if colon:
                            #subfile =  line[colon + 1:].strip()
                    #if subfile and os.path.exists(self.path(project) + subfile):
                        #newsubfile = format.filename(subfile)
                        #os.rename(self.path(project) + subfile, self.path(project) + newsubfile)
                        #subfiles.append(newsubfile)
                #firstline = False

        #return [ subfile for subfile in subfiles ] #return only the files that actually exist
        


    #def test(self,project, filename, inputformat, depth = 0):
        #printdebug("Testing " + filename)
        #o = ""       


        #if depth > 3: #security against archive-bombs
            #if os.path.exists(self.path(project) + filename):
                #os.unlink(self.path(project) + filename)
            #return ""

        #prefix = (depth + 1) * "\t"
        #remove = False
        #o += prefix + "<file name=\""+filename+"\""
        #if not os.path.exists(self.path(project) + filename):
            #o += " uploaded=\"no\" />\n"
        #else:
            #if self.isarchive(filename):
                #o += " archive=\"yes\">"
                #remove = True #archives no longer necessary after extract
            #else:
                #o += " format=\""+inputformat.__class__.__name__+"\" formatlabel=\""+inputformat.name+"\" encoding=\""+inputformat.encoding+"\""; #TODO: output nice format labels?
                #if inputformat.validate(self.path(project) + filename):
                    #o += " validated=\"yes\" />\n"
                    #printlog("Succesfully validated '" + filename + "'" )
                #else:
                    #o += " validated=\"no\" />\n"
                    #printlog("File did not validate '" + filename + "'" )
                    #remove = True #remove files that don't validate
            
            #if self.isarchive(filename):            
                #for subfilename in self.extract(project,filename, inputformat):
                    #if subfilename[-1] != '/': #only act on files, not directories
                        #printdebug("Extracted from archive: " + subfilename)
                        #if not inputformat.archivesubdirs and os.path.dirname(subfilename) != '':
                            ##we don't want subdirectories, move the files:
                            ##TODO: delete subdirectories
                            #printdebug("Moving extracted file out of subdirectory...")
                            #os.rename(self.path(project) + subfilename, self.path(project) + os.path.basename(subfilename))
                            #o += self.test(project,os.path.basename(subfilename), inputformat, depth + 1)
                        #else:
                            #o += self.test(project,subfilename, inputformat, depth + 1)
                #o += prefix + "</file>\n"    

        #if remove and os.path.exists(self.path(project) + filename):
           #printdebug("Removing '" + filename + "'" )
           #os.unlink(self.path(project) + filename)

        #return o


    #@requirelogin
    #def POST(self, project, user=None): #OBSOLETE!
        ##postdata = web.input()

        ##defaults (max 25 uploads)
        #kwargs = {}
        #for i in range(1,26):    
            #kwargs['upload' + str(i)] = {}                            
        #postdata = web.input(**kwargs)
        #if not 'uploadcount' in postdata or not postdata['uploadcount'].isdigit():
            #raise BadRequest('No valid uploadcount specified') #TODO: message doesn't show to client
        #if int(postdata['uploadcount']) > 25:
            #raise BadRequest('Too many uploads') #TODO: message doesn't show to client

        ##Check if all uploads have a valid format specified, raise 403 otherwise, dismissing any uploads
        #for i in range(1,int(postdata['uploadcount']) + 1):
            #if 'upload'+str(i) in postdata or ('uploadfilename'+str(i) in postdata and 'uploadtext' + str(i) in postdata):
                #inputformat = None
                #if not 'uploadformat' + str(i) in postdata:
                    #raise BadRequest('No upload format specified') #TODO: message doesn't show to client
                #for f in settings.INPUTFORMATS:                
                    #if f.__class__.__name__ == postdata['uploadformat' + str(i)]:
                        #inputformat = f
            
                #if not inputformat:
                    #raise web.forbidden() 
            #else:
                #raise web.forbidden()

        #Project.create(project, user)


        #web.header('Content-Type', "text/xml; charset=UTF-8")
        #output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        #output += "<clamupload uploads=\""+str(postdata['uploadcount'])+"\">\n"

        ##we may now assume all upload-data exists:
        #for i in range(1,int(postdata['uploadcount']) + 1):
            #if 'upload'+str(i) in postdata and (not 'uploadtext'+str(i) in postdata or not postdata['uploadtext' + str(i)]) and (not 'uploadurl'+str(i) in postdata or not postdata['uploadurl' + str(i)]):
                #output += "<upload seq=\""+str(i) +"\" filename=\""+postdata['upload' + str(i)].filename +"\">\n"

                #printdebug("Selecting client-side file " + postdata['upload' + str(i)].filename + " for upload")

                #filename = os.path.basename(postdata['upload' + str(i)].filename.lower())

                ##Is the upload an archive?
                #extension = filename.split(".")[-1]
                #if extension == "gz" or  extension == "bz2" or extension == "tar" or  extension == "zip":
                    #archive = True
                #else:                
                    ##upload not an archive:
                    #archive = False
                    #filename = inputformat.filename(filename) #set proper filename extension
                #realupload = True
                #wget = False
            #elif 'uploadtext'+str(i) in postdata and postdata['uploadtext' + str(i)]:
                #if 'uploadfilename'+str(i) in postdata and postdata['uploadfilename' + str(i)]:
                    #filename = postdata['uploadfilename' + str(i)]
                #else:
                    ##if no filename exists, make a random one
                    #filename =  "%032x" % random.getrandbits(128)
                #output += "<upload seq=\""+str(i) +"\" filename=\""+postdata['uploadfilename' + str(i)] +"\">\n"

                #archive = False
                #filename = inputformat.filename(postdata['uploadfilename' + str(i)]) #set proper filename extension
                #realupload = False
                #wget = False
            #elif 'uploadurl'+str(i) in postdata and postdata['uploadurl' + str(i)]:
                #if 'uploadfilename'+str(i) in postdata and postdata['uploadfilename' + str(i)]:
                    ##explicit filename passed
                    #filename = postdata['uploadfilename' + str(i)]
                #else:
                    ##get filename from URL:
                    #filename = os.path.basename(postdata['uploadurl' + str(i)])
                    #if not filename:
                        #filename =  "%032x" % random.getrandbits(128)  #make a random one

                #output += "<upload seq=\""+str(i) +"\" filename=\""+postdata['uploadurl' + str(i)] +"\">\n"

                #wget = True
                #realupload = False
                #filename = inputformat.filename(filename) #set proper filename extension


            #inputformat = None
            #for f in settings.INPUTFORMATS:                
                #if f.__class__.__name__ == postdata['uploadformat' + str(i)]:
                    #inputformat = f

            ##write trigger so the system knows uploads are in progress
            ##f = open(Project.path(project) + '.upload','w') 
            ##f.close()

            #printlog("Uploading '" + filename + "' (" + unicode(inputformat) + ", " + inputformat.encoding + ")")
            #printdebug("(start copy upload)" )
            ##upload file 
            ##if archive:
            #if inputformat.subdirectory:
                #if not os.path.isdir(inputformat.subdirectory ):
                    #os.mkdir(inputformat.subdirectory ) #TODO: make recursive and set mode
                #filename = inputformat.subdirectory  + "/" + filename
    
            #if wget:
                #try:
                    #req = urllib2.urlopen(postdata['uploadurl' + str(i)])
                #except:
                    #raise web.webapi.NotFound()
                #CHUNK = 16 * 1024
                #f = open(Project.path(project) + 'input/' + filename,'wb')
                #while True:
                    #chunk = req.read(CHUNK)
                    #if not chunk: break
                    #f.write(chunk)
            #elif realupload:
                #f = open(Project.path(project) + 'input/' + filename,'wb')
                #for line in postdata['upload' + str(i)].file:
                    #f.write(line) #encoding unaware, solves big-file upload problem?
            #else:
                #f = codecs.open(Project.path(project) + 'input/' + filename,'w', inputformat.encoding)
                #f.write(postdata['uploadtext' + str(i)])
            #f.close()
            #printdebug("(end copy upload)" )

            ##test uploaded files (this also takes care of extraction)
            #output += self.test(project, filename, inputformat)
            
            #output += "</upload>\n"

        #output += "</clamupload>"
         
        #return output #200


def sufficientresources():
    if settings.REQUIREMEMORY > 0:
        if not os.path.exists('/proc/meminfo'):
            printlog("WARNING: No /proc/meminfo available on your system! Not Linux? Skipping memory requirement check!")
        else:
            memfree = cached = 0
            f = open('/proc/meminfo')
            for line in f:
                if line[0:8] == "MemFree:":                    
                    memfree = float(line[9:].replace('kB','').strip()) #in kB
                if line[0:8] == "Cached:":                    
                    cached = float(line[9:].replace('kB','').strip()) #in kB
            f.close()
            if settings.REQUIREMEMORY * 1024 > memfree + cached:
                return False                                
    if settings.MAXLOADAVG > 0:
        if not os.path.exists('/proc/loadavg'):
            printlog("WARNING: No /proc/loadavg available on your system! Not Linux? Skipping load average check!")
        else:
            f = open('/proc/loadavg')
            line = f.readline()
            loadavg = float(line.split(' ')[0])
            f.close()
            if settings.MAXLOADAVG < loadavg:
                return False
    if settings.MINDISKSPACE and settings.DISK:
        dffile = '/tmp/df.' + str("%034x" % random.getrandbits(128))
        ret = os.system('df -m ' + settings.DISK + " | gawk '{ print $4; }'  > " + dffile)
        if ret == 0:
            try:
                f = open(dffile,'r')
                free = int(f.readlines()[-1])
                f.close()
                if free < settings.MINDISKFREE:
                    os.unlink(dffile)
                    return False
            except:
                printlog("WARNING: df " + settings.DISK + " failed (unexpected format). Skipping disk space check!")                                                
                os.unlink(dffile)

        else:
            printlog("WARNING: df " + settings.DISK + " failed. Skipping disk space check!")        
    return True
        


def usage():
        print >> sys.stderr, "Syntax: clamservice.py [options] clam.config.yoursystem"
        print >> sys.stderr, "Options:"
        print >> sys.stderr, "\t-d            - Enable debug mode"
        print >> sys.stderr, "\t-c            - Run in FastCGI mode"
        print >> sys.stderr, "\t-H [hostname] - Hostname"
        print >> sys.stderr, "\t-p [port]     - Port"
        print >> sys.stderr, "\t-h            - This help message"
        print >> sys.stderr, "\t-v            - Version information"
        print >> sys.stderr, "(Note: Do not invoke clamservice directly if you want to run in WSGI mode)"


def set_defaults(HOST = None, PORT = None):
    global LOG

    #Default settings
    settingkeys = dir(settings)

    if 'ROOT' in settingkeys and not settings.ROOT[-1] == "/":
        settings.ROOT += "/" #append slash
    if not 'USER' in settingkeys:
        settings.USER = None
    if not 'ADMINS' in settingkeys:
        settings.ADMINS = []
    if not 'PROJECTS_PUBLIC' in settingkeys:
        settings.PROJECTS_PUBLIC = True
    if not 'PROFILES' in settingkeys:
        settings.PROFILES = []
    if not 'INPUTSOURCES' in settingkeys:
        settings.INPUTSOURCES = []
    if not 'PORT' in settingkeys and not PORT:
        settings.PORT = 80
    if not 'HOST' in settingkeys and not HOST:
        settings.HOST = os.uname()[1]
    if not 'URLPREFIX' in settingkeys:
        settings.URLPREFIX = ''            
    if not 'REQUIREMEMORY' in settingkeys:
        settings.REQUIREMEMORY = 0 #unlimited
    if not 'MAXLOADAVG' in settingkeys:
        settings.MAXLOADAVG = 0 #unlimited
    if not 'MINDISKSPACE' in settingkeys:
        settings.MINDISKSPACE = 0
    if not 'DISK' in settingkeys:
        settings.DISK = None    
    if not 'STYLE' in settingkeys:
        settings.STYLE = 'classic'
    if not 'CLAMDIR' in settingkeys:
        settings.CLAMDIR = os.path.dirname(sys.argv[0])
    if not 'DISPATCHER' in settingkeys:
        settings.DISPATCHER = 'clamdispatcher.py'
    if not 'REALM' in settingkeys:
        settings.REALM = settings.SYSTEM_ID
    if not 'ENABLEWEBAPP' in settingkeys:
        settings.ENABLEWEBAPP = True
    elif settings.ENABLEWEBAPP is False:
        Project.GHOST = True
        Index.GHOST = True        
    if not 'WEBSERVICEGHOST' in settingkeys:
        settings.WEBSERVICEGHOST = False        
    elif settings.WEBSERVICEGHOST:
        CLAMService.urls = (
            '/' + settings.WEBSERVICEGHOST + '/', 'IndexGhost',
            '/' + settings.WEBSERVICEGHOST + '/([A-Za-z0-9_]*)/?', 'ProjectGhost',
            '/' + settings.WEBSERVICEGHOST + '/([A-Za-z0-9_]*)/upload/?', 'Uploader',
            '/' + settings.WEBSERVICEGHOST + '/([A-Za-z0-9_]*)/output/(.*)/?', 'OutputFileHandler', #(also handles viewers, convertors, metadata, and archive download
            '/' + settings.WEBSERVICEGHOST + '/([A-Za-z0-9_]*)/input/(.*)/?', 'InputFileHandler',
            #'/([A-Za-z0-9_]*)/output/([^/]*)/([^/]*)/?', 'ViewerHandler
        ) + CLAMService.urls
    if not 'REMOTEHOST' in settingkeys:
        settings.REMOTEHOST = None
    elif not 'REMOTEUSER' in settingkeys:
        settings.REMOTEUSER = None
    if not 'PREAUTHHEADER' in settingkeys:
        settings.PREAUTHHEADER = None         
    if not 'PREAUTHMAPPINGS' in settingkeys:
        settings.PREAUTHMAPPINGS = None 
    if not 'USERS_MYSQL' in settingkeys:
        settings.USERS_MYSQL = None

    if 'LOG' in settingkeys: #set LOG
        LOG = open(settings.LOG,'a')

    for s in ['SYSTEM_ID','SYSTEM_DESCRIPTION','SYSTEM_NAME','ROOT','COMMAND','PROFILES']:    
        if not s in settingkeys:
            error("ERROR: Service configuration incomplete, missing setting: " + s)


def test_dirs():
    if not os.path.isdir(settings.ROOT):
        warning("Root directory does not exist yet, creating...")
        os.mkdir(settings.ROOT)
    if not os.path.isdir(settings.ROOT + 'projects'):
        warning("Projects directory does not exist yet, creating...")
        os.mkdir(settings.ROOT + 'projects')    
    elif not settings.PARAMETERS:
            warning("No parameters specified in settings module!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    settingsmodule = None
    fastcgi = False
    PORT = HOST = None


    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdcH:p:v")
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-d':
            DEBUG = True
            setdebug(True)
        elif o == '-c':
            fastcgi = True
        elif o == '-H':
            HOST = a
        elif o == '-p':
            PORT = int(a)
        elif o == '-h':
            usage()
            sys.exit(0)
        elif o == '-v':
            print "CLAM WebService version " + str(VERSION)
            sys.exit(0)
        else:
            usage()
            print "ERROR: Unknown option: ", o
            sys.exit(2)

    if (len(args) == 1):
        settingsmodule = args[0]
    elif (len(args) > 1):
        print >>sys.stderr, "ERROR: Too many arguments specified"
        usage()
        sys.exit(2)
    else:
        print >>sys.stderr, "ERROR: No settings module specified!"
        usage()
        sys.exit(2)



    


    import_string = "import " + settingsmodule + " as settings"
    exec import_string

    #Check version
    req = str(settings.REQUIRE_VERSION).split('.')
    ver = str(VERSION).split('.')

    uptodate = True
    for i in range(0,len(req)):
        if i < len(ver):
            if req[i] > ver[i]:
                uptodate = False
                break
            elif ver[i] > req[i]:
                break
    if not uptodate:
        error("Version mismatch: at least " + str(settings.REQUIRE_VERSION) + " is required")


    set_defaults(HOST,PORT)
    if HOST:
        settings.HOST = HOST
    test_dirs()

    #fake command line options for web.py
    sys.argv = [ sys.argv[0] ] 
    if PORT:
        sys.argv.append(str(PORT)) #port from command line
        settings.PORT = PORT                       
    elif 'PORT' in dir(settings):
        sys.argv.append(str(settings.PORT))

    # Create decorator
    #requirelogin = real_requirelogin #fool python :) 
    #if USERS:
    #    requirelogin = digestauth.auth(lambda x: USERS[x], realm=SYSTEM_ID)
    if settings.USERS:
        auth = clam.common.digestauth.auth(userdb_lookup_dict, realm= settings.REALM)
    elif settings.USERS_MYSQL:
        validate_users_mysql()
        auth = clam.common.digestauth.auth(userdb_lookup_mysql, realm= settings.REALM)    
        

    if not fastcgi:
        if settings.URLPREFIX:
            raise Exception("Can't use URLPREFIX when running in standalone mode!")
        settings.URLPREFIX = '' #standalone server always runs at the root

    CLAMService('fastcgi' if fastcgi else '') #start

def run_wsgi(settings_module):
    """Run CLAM in WSGI mode"""
    global settingsmodule
    #import_string = "import " + settingsmodule + " as settings"
    #exec import_string


    globals()['settings'] = settings_module
    settingsmodule = settings_module.__name__
    
    setlog(None)
    set_defaults(None,None)
    test_dirs()

    if settings.USERS:
        auth = clam.common.digestauth.auth(userdb_lookup_dict, realm= settings.REALM)
    elif settings.USERS_MYSQL:
        validate_users_mysql()
        auth = clam.common.digestauth.auth(userdb_lookup_mysql, realm= settings.REALM)            

    service = CLAMService('wsgi')
    return service.application


