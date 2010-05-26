#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Webservice --
#       by Maarten van Gompel (proycon)
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
from copy import copy #shallow copy (use deepcopy for deep)
from functools import wraps


sys.path.append(sys.path[0] + '/..')
os.environ['PYTHONPATH'] = sys.path[0] + '/..'

import clam.common.status 
import clam.common.parameters
import clam.common.formats
import clam.common.digestauth
import clam.config.defaults as settings #will be overridden by real settings later

#Maybe for later: HTTPS support
#web.wsgiserver.CherryPyWSGIServer.ssl_certificate = "path/to/ssl_certificate"
#web.wsgiserver.CherryPyWSGIServer.ssl_private_key = "path/to/ssl_private_key"


VERSION = '0.2.6'

DEBUG = False
    
DATEMATCH = re.compile(r'^[\d\.\-\s:]*$')
#Empty defaults
#SYSTEM_ID = "clam"
#SYSTEM_NAME = "CLAM: Computional Linguistics Application Mediator"
#SYSTEM_DESCRIPTION = "CLAM is a webservice wrapper around NLP tools"
#COMMAND = ""
#ROOT = "."
#PARAMETERS = []
#INPUTFORMATS = []
#OUTPUTFORMATS = []
#URL = "http://localhost:8080"
#USERS = None

def printlog(msg):
    now = datetime.datetime.now()
    print "------------------- [" + now.strftime("%d/%b/%Y %H:%M:%S") + "] " + msg 

def printdebug(msg):
    global DEBUG
    if DEBUG: printlog("DEBUG: " + msg)
        

class BadRequest(web.webapi.HTTPError):
    """`400 Bad Request` error."""
    def __init__(self, message = "Bad request"):
        status = "400 Bad Request"
        headers = {'Content-Type': 'text/html'}
        super(BadRequest,self).__init__(status, headers, message)

TEMPUSER = '' #temporary global variable (not very elegant and not thread-safe!) #TODO: improve?
def userdb_lookup(user, realm):
    global TEMPUSER
    TEMPUSER = user
    return settings.USERS[user] #possible KeyError is captured by digest.auth itself!

#requirelogin = lambda x: x
#if settings.USERS:
#    requirelogin = clam.common.digestauth.auth(userdb_lookup, realm= settings.SYSTEM_ID)

auth = lambda x: x

#auth = clam.common.digestauth.auth(userdb_lookup, realm= settings.SYSTEM_ID)

def requirelogin(f):
    global TEMPUSER, auth
    def wrapper(*args, **kwargs):
        printdebug("wrapper:"+ repr(f))        
        args = list(args)
        args.append(TEMPUSER)
        args = tuple(args)
        if settings.USERS:
            #f = clam.common.digestauth.auth(userdb_lookup, realm=settings.SYSTEM_ID)(f)       
            return auth(f)(*args, **kwargs)
        else:
            return f(*args, **kwargs)
    return wraps(f)(wrapper)

class JobService(object):

    urls = (
    '/', 'Index',
    '/([A-Za-z0-9_]*)/?', 'Project',
    '/([A-Za-z0-9_]*)/upload/?', 'Uploader',
    '/([A-Za-z0-9_]*)/output/?', 'OutputInterface',
    '/([A-Za-z0-9_]*)/output/(.*)', 'OutputFileHandler',
    '/([A-Za-z0-9_]*)/input/(.*)', 'InputFileHandler',
    )


    def __init__(self):
        global VERSION    
        printlog("Starting CLAM JobService, version " + str(VERSION) + " ...")
        if not settings.ROOT or not os.path.isdir(settings.ROOT):
            print >>sys.stderr,"ERROR: Specified root path " + settings.ROOT + " not found"                 
            sys.exit(1)
        elif not settings.COMMAND.split(" ")[0] or os.system("which " + settings.COMMAND.split(" ")[0] + "> /dev/null 2> /dev/null") != 0:
            print >>sys.stderr,"ERROR: Specified command " + settings.COMMAND.split(" ")[0] + " not found"                 
            sys.exit(1)            
        #elif not settings.INPUTFORMATS:
        #    print >>sys.stderr,"ERROR: No inputformats specified!"
        #    sys.exit(1)            
        #elif not settings.OUTPUTFORMATS:
        #    print >>sys.stderr,"ERROR: No outputformats specified!"
        #    sys.exit(1)            
        elif not settings.PARAMETERS:
            print >>sys.stderr,"WARNING: No parameters specified in settings module!"
        else:      
            lastparameter = None      
            try:
                for parametergroup, parameters in settings.PARAMETERS:
                    for parameter in parameters:
                        assert isinstance(parameter, clam.common.parameters.AbstractParameter)
                        lastparameter = parameter
            except AssertionError:
                print >>sys.stderr,"ERROR: Syntax error in parameter specification."
                if lastparameter:            
                    print >>sys.stderr,"Last part parameter: ", lastparameter.id
                sys.exit(1)            
            
        self.service = web.application(self.urls, globals())
        self.service.internalerror = web.debugerror
        self.service.run()

    @staticmethod
    def corpusindex(): 
            """Get list of pre-installed corpora"""
            corpora = []
            for f in glob.glob(settings.ROOT + "corpora/*"):
                if os.path.isdir(f):
                    corpora.append(os.path.basename(f))
            return corpora

    @staticmethod
    def inputformats(name="inputformat"):
        """Renders a list of input formats"""
        #MAYBE TODO: add selected?
        render = web.template.render('templates')
        return render.inputformats(name, [ (format.__class__.__name__, unicode(format) ) for format in settings.INPUTFORMATS ])
    


class Index(object):
    @requirelogin
    def GET(self, user = None):
        """Get list of projects"""
        projects = []
        for f in glob.glob(settings.ROOT + "projects/*"):
            if os.path.isdir(f):
                projects.append(os.path.basename(f))

        errors = "no"
        errormsg = ""

        corpora = JobService.corpusindex()

        render = web.template.render('templates')
        return render.response(VERSION, settings.SYSTEM_ID, settings.SYSTEM_NAME, settings.SYSTEM_DESCRIPTION, user, None, settings.URL, -1 ,"",[],0, errors, errormsg, settings.PARAMETERS,corpora, None,None, settings.OUTPUTFORMATS, settings.INPUTFORMATS, None, projects )
        


class Project(object):

    @staticmethod
    def path(project):
        """Get the path to the project (static method)"""
        return settings.ROOT + "projects/" + project + "/"

    @staticmethod
    def create(project, user):         
        """Create project skeleton if it does not already exist (static method)"""
        printdebug("Checking if " + settings.ROOT + "projects/" + project + " exists") 
        if not project:
            raise BadRequest('Empty project name!') 
        if not os.path.isdir(settings.ROOT + "projects/" + project):
            printlog("Creating project '" + project + "'")
            os.mkdir(settings.ROOT + "projects/" + project)
            os.mkdir(settings.ROOT + "projects/" + project + "/input")
            os.mkdir(settings.ROOT + "projects/" + project + "/output")
            if 'PROJECTS_PUBLIC' in dir(settings) and not settings.PROJECTS_PUBLIC:
                f = codecs.open(settings.ROOT + "projects/" + project + '/.users','w','utf-8')                         
                f.write(user + "\n")
                f.close()

    @staticmethod
    def access(project, user):
        """Checks whether the specified user has access to the project"""
        userfile = Project.path(project) + ".users"
        if os.path.isfile(userfile):
            access = False
            f = codecs.open(userfile,'r','utf-8')
            for line in f:
                line = line.strip()
                if line and user == line.strip():
                    access = True
                    break
            f.close()
            return access
        else:
            return True #no access file, grant access for all users

    def pid(self, project):
        pidfile = Project.path(project) + '.pid'
        if os.path.isfile(pidfile):
            f = open(pidfile,'r')
            pid = int(f.read(os.path.getsize(pidfile)))
            f.close()
            return pid
        else:
            return 0

    def running(self,project):
        pid = self.pid(project)
        if pid == 0:
            return False
        #printdebug("Polling process " + str(pid) + ", still running?" ) 
        done = False
        statuscode = 0
        try:
            returnedpid, statuscode = os.waitpid(pid, os.WNOHANG)
            if returnedpid == 0:
                return True
        except OSError: #no such process
            done = True            
        if done or returnedpid == pid:
            if os.path.isfile(Project.path(project) + ".pid"):
                f = open(Project.path(project) + ".done",'w')
                f.write(str(statuscode)) #non-zero exit codes are interpreted as errors!
                f.close()
                os.unlink(Project.path(project) + ".pid")
            return False        
    
    def abort(self,project):
        if self.pid(project) == 0:
            return False
        try:
            printlog("Aborting process in project '" + project + "'" )
            os.kill(self.pid(project), 15)
            os.unlink(Project.path(project) + ".pid")
            return True
        except:
            return False  

    def done(self,project):
        return os.path.isfile(Project.path(project) + ".done")

    def exitstatus(self, project):
        f = open(Project.path(project) + ".done")
        status = int(f.read(1024))
        f.close()
        return status

    def preparingdownload(self,project):
        return os.path.isfile(Project.path(project) + ".download")

    def processingupload(self,project):
        return os.path.isfile(Project.path(project) + ".upload")

    def exists(self, project):
        """Check if the project exists"""
        printdebug("Checking if " + settings.ROOT + "projects/" + project + " exists") 
        return os.path.isdir(Project.path(project))

    def statuslog(self,project):
        statuslog = []
        statusfile = Project.path(project) + ".status"
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

    def status(self, project):
        global DATEMATCH
        if self.running(project):
            statuslog, completion = self.statuslog(project)
            if statuslog:
                return (clam.common.status.RUNNING, statuslog[0][0],statuslog, completion)
            else:
                return (clam.common.status.RUNNING, "The system is running",  [], 0) #running
        elif self.done(project):
            statuslog, completion = self.statuslog(project)
            if statuslog:
                return (clam.common.status.DONE, statuslog[0][0],statuslog, completion)
            else:
                return (clam.common.status.DONE, "Done", statuslog, 100)
        #elif self.preparingdownload(project):
        #    return (clam.common.status.DOWNLOAD, "Preparing package for download, please wait...")
        #elif self.processingupload(project):
        #    return (clam.common.status.UPLOAD, "Processing upload, please wait...")
        else:
            return (clam.common.status.READY, "Ready to start", [], 0)


    def dirindex(self, project, formats, mode = 'output', d = ''):
        paths = []            
        for f in glob.glob(Project.path(project) + mode + "/" + d + "/*"):
            if os.path.isdir(f):
                paths = paths + [ (d + "/" + x[0],x[1],x[2]) for x in self.dirindex(project,formats, mode, d+"/"+os.path.basename(f)) ]
            else:
                filename = os.path.basename(f)
                if filename[0] == '.': continue #skip hidden files
                format = clam.common.formats.Format() #unspecified format
                for fmt in formats:
                    if fmt.match(filename):
                        format = fmt
                        break                                
                paths.append( ( os.path.basename(f), format.__class__.__name__, format.name, format.encoding ) )
        return paths

    def inputindex(self,project):        
        return self.dirindex(project,settings.INPUTFORMATS,'input')



    def outputindex(self,project, d = ''):        
        return self.dirindex(project,settings.OUTPUTFORMATS,'output')


    def response(self, user, project, parameters, datafile = False):
        global VERSION

        #check if there are invalid parameters:
        errors = "no"
        errormsg = ""

        statuscode, statusmsg, statuslog, completion = self.status(project)
        

        corpora = []
        if statuscode == clam.common.status.READY:
            corpora = JobService.corpusindex()
        else:
            corpora = []
        if statuscode == clam.common.status.DONE:
            outputpaths = self.outputindex(project)
            if self.exitstatus(project) != 0: #non-zero codes indicate errors!
                errors = "yes"
                errormsg = "An error occurred within the system. Please inspect the error log for details"
                printlog("Child process failed, exited with non zero-exit code.")
        else:
            outputpaths = []        
        if statuscode == clam.common.status.READY:
            inputpaths = self.inputindex(project)
        else:
            inputpaths = []      
        
        for parametergroup, parameterlist in parameters:
            for parameter in parameterlist:
                if parameter.error:
                    errors = "yes"
                    if not errormsg: errormsg = "One or more parameters are invalid"
                    printlog("One or more parameters are invalid")
                    break

        render = web.template.render('templates')
        return render.response(VERSION, settings.SYSTEM_ID, settings.SYSTEM_NAME, settings.SYSTEM_DESCRIPTION, user, project, settings.URL, statuscode,statusmsg, statuslog, completion, errors, errormsg, parameters,corpora, outputpaths,inputpaths, settings.OUTPUTFORMATS, settings.INPUTFORMATS, datafile, None )
        
                    
    @requirelogin
    def GET(self, project, user=None):
        """Main Get method: Get project state, parameters, outputindex"""
        if not self.exists(project):
            return web.webapi.NotFound()
        else:
            if user and not Project.access(project, user):
                return web.webapi.Unauthorized()
            return self.response(user, project, settings.PARAMETERS)


    @requirelogin
    def PUT(self, project, user=None):
        """Create an empty project"""
        Project.create(project, user)
        return "" #200

    @requirelogin
    def POST(self, project, user=None):  
        Project.create(project, user)
        if user and not Project.access(project, user):
            return web.webapi.Unauthorized()
                    
        #Generate arguments based on POSTed parameters
        params = []
        postdata = web.input()
        errors = False

        #we're going to modify parameter values, this we can't do
        #on the global variable, that won't be thread-safe, we first
        #make a (shallow) copy and act on that  
        parameters = []
        for parametergroup, parameterlist in settings.PARAMETERS:
            newparameterlist = []
            for parameter in parameterlist:
                newparameterlist.append(copy(parameter))
            parameters.append( (parametergroup, newparameterlist) ) 

        for parametergroup, parameterlist in parameters:
            for parameter in parameterlist:
                if parameter.access(user):
                    postvalue = parameter.valuefrompostdata(postdata) #parameter.id in postdata and postdata[parameter.id] != '':    
                    if not (isinstance(postvalue,bool) and postvalue == False):
                        if parameter.set(postvalue): #may generate an error in parameter.error
                            params.append(parameter.compilearg(parameter.value))
                        else:
                            if not parameter.error: parameter.error = "Something went wrong whilst settings this parameter!" #shouldn't happen
                            printlog("Unable to set " + parameter.id + ": " + parameter.error)
                            errors = True
                    elif parameter.required:
                        #Not all required parameters were filled!
                        parameter.error = "This option must be set"
                        errors = True
                    if parameter.value and (parameter.forbid or parameter.require):
                        for _, parameterlist2 in parameters:
                            for parameter2 in parameterlist2:
                                    if parameter.forbid and parameter2.id in parameter.forbid and parameter2.value:
                                        parameter.error = parameter2.error = "Setting parameter '" + parameter.name + "' together with '" + parameter2.name + "'  is forbidden"
                                        printlog("Setting " + parameter.id + " and " + parameter2.id + "' together is forbidden")
                                        errors = True
                                    if parameter.require and parameter2.id in parameter.require and not parameter2.value:
                                        parameter.error = parameter2.error = "Parameters '" + parameter.name + "' has to be set with '" + parameter2.name + "'  is"
                                        printlog("Setting " + parameter.id + " requires you also set " + parameter2.id )
                                        errors = True

        if errors:
            #There are parameter errors, return 200 response with errors marked, (tried 400 bad request, but XSL stylesheets don't render with 400)
            #raise BadRequest(unicode(self.GET(project)))
            printlog("There are errors, not starting.")
            return self.response(user, project, parameters)
        else:
            #write clam.xml output file
            render = web.template.render('templates')
            f = open(Project.path(project) + "clam.xml",'w')
            f.write(str(self.response(user, project, parameters, True)))
            f.close()



            #Start project with specified parameters
            cmd = settings.COMMAND
            cmd = cmd.replace('$PARAMETERS', " ".join(params))
            if 'usecorpus' in postdata and postdata['usecorpus']:
                corpus = postdata['usecorpus'].replace('..','') #security            
                #use a preinstalled corpus:
                if os.path.exists(settings.ROOT + "corpora/" + corpus):
                    cmd = cmd.replace('$INPUTDIRECTORY', settings.ROOT + "corpora/" + corpus + "/")
                else:
                    raise web.webapi.NotFound("Corpus " + corpus + " not found")
            else:
                cmd = cmd.replace('$INPUTDIRECTORY', Project.path(project) + 'input/')
            cmd = cmd.replace('$OUTPUTDIRECTORY',Project.path(project) + 'output/')
            cmd = cmd.replace('$STATUSFILE',Project.path(project) + '.status')
            cmd = cmd.replace('$DATAFILE',Project.path(project) + 'clam.xml')
            cmd = cmd.replace('$USERNAME',user if user else "anonymous")
            #cmd = sum([ params if x == "$PARAMETERS" else [x] for x in COMMAND ] ),[])
            #cmd = sum([ Project.path(project) + 'input/' if x == "$INPUTDIRECTORY" else [x] for x in COMMAND ] ),[])        
            #cmd = sum([ Project.path(project) + 'output/' if x == "$OUTPUTDIRECTORY" else [x] for x in COMMAND ] ),[])        
            #TODO: protect against insertion
            if settings.COMMAND.find("2>") == -1:
                cmd += " 2> " + Project.path(project) + "output/error.log" #add error output
            printlog("Starting " + settings.COMMAND + ": " + repr(cmd) + " ..." )
            process = subprocess.Popen(cmd,cwd=Project.path(project), shell=True)				
            if process:
                pid = process.pid
                printlog("Started with pid " + str(pid) )
                f = open(Project.path(project) + '.pid','w')
                f.write(str(pid))
                f.close()
                return self.response(user, project, parameters) #return 200 -> GET
            else:
                raise web.webapi.InternalError("Unable to launch process")

    @requirelogin
    def DELETE(self, project, user=None):
        if not self.exists(project):
            return web.webapi.NotFound()
        statuscode, _, _, _  = self.status(project)
        if statuscode == clam.common.status.RUNNING:
            self.abort(project)   
        printlog("Deleting project '" + project + "'" )
        shutil.rmtree(Project.path(project))
        return "" #200

class OutputFileHandler(object):

    @requirelogin
    def GET(self, project, filename, user=None):    
        path = Project.path(project) + "output/" + filename.replace("..","")
        
        #TODO: find outputformat?

        if os.path.isfile(path): 
            for line in open(path,'r'): 
                yield line
        elif os.path.isdir(path): 
            for f in glob.glob(path + "/*"):
                yield os.path.basename(f)                
        else:
            raise web.webapi.NotFound()

class InputFileHandler(object):

    @requirelogin
    def GET(self, project, filename, user=None):    
        path = Project.path(project) + "input/" + filename.replace("..","")
        
       
        if os.path.isfile(path): 
            for line in open(path,'r'): 
                yield line
        elif os.path.isdir(path): 
            for f in glob.glob(path + "/*"):
                yield os.path.basename(f)                
        else:
            raise web.webapi.NotFound()

    @requirelogin
    def DELETE(self, project, filename, user=None):    
        if len(filename.replace("..","")) == 0:
            raise BadRequest('No file specified') #TODO: message won't show

        path = Project.path(project) + "input/" + filename.replace("..","")
        
        if os.path.isfile(path): 
            os.unlink(path)
        elif os.path.isdir(path): 
            shutil.rmtree(path)
        else:
            raise web.webapi.NotFound()

class OutputInterface(object):

    @requirelogin        
    def GET(self, project, user=None):
        """Generates and returns a download package (or 403 if one is already in the process of being prepared)"""
        if os.path.isfile(Project.path(project) + '.download'):
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
                if os.path.isfile(Project.path(project) + "output/" + project + ".tar.gz"):
                    os.unlink(Project.path(project) + "output/" + project + ".tar.gz")
                if os.path.isfile(Project.path(project) + "output/" + project + ".tar.bz2"):
                    os.unlink(Project.path(project) + "output/" + project + ".tar.bz2")
            elif format == 'tar.gz':
                contenttype = 'application/x-tar'
                contentencoding = 'gzip'
                command = "/bin/tar -czf"
                if os.path.isfile(Project.path(project) + "output/" + project + ".zip"):
                    os.unlink(Project.path(project) + "output/" + project + ".zip")
                if os.path.isfile(Project.path(project) + "output/" + project + ".tar.bz2"):
                    os.unlink(Project.path(project) + "output/" + project + ".tar.bz2")
            elif format == 'tar.bz2': 
                contenttype = 'application/x-bzip2'
                command = "/bin/tar -cjf"
                if os.path.isfile(Project.path(project) + "output/" + project + ".tar.gz"):
                    os.unlink(Project.path(project) + "output/" + project + ".tar.gz")
                if os.path.isfile(Project.path(project) + "output/" + project + ".zip"):
                    os.unlink(Project.path(project) + "output/" + project + ".zip")
            else:
                raise BadRequest('Invalid archive format') #TODO: message won't show

            path = Project.path(project) + "output/" + project + "." + format
            
            if not os.path.isfile(path):
                printlog("Building download archive in " + format + " format")
                cmd = command + ' ' + project + '.' + format + ' *'
                printdebug(cmd)
                printdebug(Project.path(project)+'output/')
                process = subprocess.Popen(cmd, cwd=Project.path(project)+'output/', shell=True)	        			
                if not process:
                    raise web.webapi.InternalError("Unable to make download package")                
                else:
                    pid = process.pid
                    f = open(Project.path(project) + '.download','w') 
                    f.write(str(pid))
                    f.close()
                    os.waitpid(pid, 0) #wait for process to finish
                    os.unlink(Project.path(project) + '.download')

            if contentencoding:
                web.header('Content-Encoding', contentencoding)
            web.header('Content-Type', contenttype)
            for line in open(path,'r'):
                yield line
               
    #@requirelogin
    #def POST(self, project, user=None):
    #    """Trigger generation of download package"""
    #    if not os.path.isfile(Project.path(project) + '.download'):
    #        postdata = web.input() 
    #        if 'format' in postdata:
    #            format = postdata['format']
    #        else:
    #            format = 'zip' #default          
    #        cmd = ['tools/make-download-package.sh', project] #call processing chain 
    #        process = subprocess.Popen(cmd, cwd=Project.path(project))	        			
    #        if process:
    #            pid = process.pid
    #            f = open(Project.path(project) + '.download','w') 
    #            f.write(str(pid))
    #            f.close()
    #        else:
    #            raise web.webapi.InternalError("Unable to make download package")                
    #    return "" #200  

    @requirelogin
    def DELETE(self, project, user=None):          
        """Reset system, delete all output files and prepare for a new run"""
        d = Project.path(project) + "output"
        if os.path.isdir(d):
            shutil.rmtree(d)
            os.mkdir(d)
        if os.path.exists(Project.path(project) + ".done"):
            os.unlink(Project.path(project) + ".done")                       
        if os.path.exists(Project.path(project) + ".status"):
            os.unlink(Project.path(project) + ".status")                       

class Uploader(object):

    def path(self, project):
        return Project.path(project) + 'input/'

    def isarchive(self,filename):
        return (filename[-3:] == '.gz' or filename[-4:] == '.bz2' or filename[-4:] == '.zip')

    def extract(self,project,filename, format):
        namelist = None
        subfiles = []
        if filename[-7:].lower() == '.tar.gz':
            cmd = 'tar -xvzf'
            namelist = 'tar'
        elif filename[-7:].lower() == '.tar.bz2':
            cmd = 'tar -xvjf'
            namelist = 'tar'
        elif filename[-3:].lower() == '.gz':
            cmd = 'gunzip'
            subfiles = [filename[-3:]]  #one subfile only
        elif filename[-4:].lower() == '.bz2':
            cmd = 'bunzip2'
            subfiles = [filename[-3:]] #one subfile only
        elif filename[-4:].lower() == '.tar':
            cmd = 'tar -xvf'
            namelist = 'tar'
        elif filename[-4:].lower() == '.zip':
            cmd = 'unzip -u'
            namelist = 'zip'
        else:
            raise Exception("Invalid archive format") #invalid archive, shouldn't happend

        printlog("Extracting '" + filename + "'" )            
        try:
            process = subprocess.Popen(cmd + " " + filename, cwd=self.path(project), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        except:
            raise web.webapi.InternalError("Unable to extract file: " + cmd + " " + filename + ", cwd="+ self.path(project))       
        out, err = process.communicate() #waits for process to end 

        if namelist:
            firstline = True
            for line in out.split("\n"):    
                line = line.strip()        
                if line:
                    subfile = None
                    if namelist == 'tar':
                        subfile = line
                    elif namelist == 'zip' and not firstline: #firstline contains archive name itself, skip it
                        colon = line.find(":")
                        if colon:
                            subfile =  line[colon + 1:].strip()
                    if subfile and os.path.exists(self.path(project) + subfile):
                        newsubfile = format.filename(subfile)
                        os.rename(self.path(project) + subfile, self.path(project) + newsubfile)
                        subfiles.append(newsubfile)
                firstline = False

        return [ subfile for subfile in subfiles ] #return only the files that actually exist
        


    def test(self,project, filename, inputformat, depth = 0):
        printdebug("Testing " + filename)
        o = ""       
        #inputformat = None
        #for f in INPUTFORMATS:
        #    if f.__class__.name == format_id:
        #        inputformat = f

        if depth > 3: #security against archive-bombs
            if os.path.exists(self.path(project) + filename):
                os.unlink(self.path(project) + filename)
            return ""

        prefix = (depth + 1) * "\t"
        remove = False
        o += prefix + "<file name=\""+filename+"\""
        if not os.path.exists(self.path(project) + filename):
            o += " uploaded=\"no\" />\n"
        else:
            if self.isarchive(filename):
                o += " archive=\"yes\">"
                remove = True #archives no longer necessary after extract
            else:
                o += " format=\""+inputformat.__class__.__name__+"\" formatlabel=\""+inputformat.name+"\" encoding=\""+inputformat.encoding+"\""; #TODO: output nice format labels?
                if inputformat.validate(self.path(project) + filename):
                    o += " validated=\"yes\" />\n"
                    printlog("Succesfully validated '" + filename + "'" )
                else:
                    o += " validated=\"no\" />\n"
                    printlog("File did not validate '" + filename + "'" )
                    remove = True #remove files that don't validate
            
            if self.isarchive(filename):            
                for subfilename in self.extract(project,filename, inputformat):
                    if subfilename[-1] != '/': #only act on files, not directories
                        printdebug("Extracted from archive: " + subfilename)
                        if not inputformat.archivesubdirs and os.path.dirname(subfilename) != '':
                            #we don't want subdirectories, move the files:
                            #TODO: delete subdirectories
                            printdebug("Moving extracted file out of subdirectory...")
                            os.rename(self.path(project) + subfilename, self.path(project) + os.path.basename(subfilename))
                            o += self.test(project,os.path.basename(subfilename), inputformat, depth + 1)
                        else:
                            o += self.test(project,subfilename, inputformat, depth + 1)
                o += prefix + "</file>\n"    

        if remove and os.path.exists(self.path(project) + filename):
           printdebug("Removing '" + filename + "'" )
           os.unlink(self.path(project) + filename)

        return o

    @requirelogin
    def GET(self, project, user=None):
        #Crude upload form
        return '<html><head></head><body><form method="POST" enctype="multipart/form-data" action=""><input type="hidden" name="uploadcount" value="1"><input type="file" name="upload1" /><br />' + str(JobService.inputformats('uploadformat1')) + '<br/><input type="submit" /></form></body></html>'

    @requirelogin
    def POST(self, project, user=None):
        #postdata = web.input()

        #defaults (max 25 uploads)
        kwargs = {}
        for i in range(1,26):    
            kwargs['upload' + str(i)] = {}                            
        postdata = web.input(**kwargs)
        if not 'uploadcount' in postdata or not postdata['uploadcount'].isdigit():
            raise BadRequest('No valid uploadcount specified') #TODO: message doesn't show to client
        if int(postdata['uploadcount']) > 25:
            raise BadRequest('Too many uploads') #TODO: message doesn't show to client

        #Check if all uploads have a valid format specified, raise 403 otherwise, dismissing any uploads
        for i in range(1,int(postdata['uploadcount']) + 1):
            if 'upload'+str(i) in postdata or ('uploadfilename'+str(i) in postdata and 'uploadtext' + str(i) in postdata):
                inputformat = None
                if not 'uploadformat' + str(i) in postdata:
                    raise BadRequest('No upload format specified') #TODO: message doesn't show to client
                for f in settings.INPUTFORMATS:                
                    if f.__class__.__name__ == postdata['uploadformat' + str(i)]:
                        inputformat = f
            
                if not inputformat:
                    raise web.forbidden() 
            else:
                raise web.forbidden()

        Project.create(project, user)

        output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        #output += "<?xml-stylesheet type=\"text/xsl\" href=\"" + settings.URL + "/static/interface.xsl\"?>\n"
        output += "<clamupload uploads=\""+str(postdata['uploadcount'])+"\">\n"

        #we may now assume all upload-data exists:
        for i in range(1,int(postdata['uploadcount']) + 1):
            if 'upload'+str(i) in postdata and (not 'uploadtext'+str(i) in postdata or not postdata['uploadtext' + str(i)]) and (not 'uploadurl'+str(i) in postdata or not postdata['uploadurl' + str(i)]):
                output += "<upload seq=\""+str(i) +"\" filename=\""+postdata['upload' + str(i)].filename +"\">\n"

                printdebug("Selecting client-side file " + postdata['upload' + str(i)].filename + " for upload")

                filename = os.path.basename(postdata['upload' + str(i)].filename.lower())

                #Is the upload an archive?
                extension = filename.split(".")[-1]
                if extension == "gz" or  extension == "bz2" or extension == "tar" or  extension == "zip":
                    archive = True
                else:                
                    #upload not an archive:
                    archive = False
                    filename = inputformat.filename(filename) #set proper filename extension
                realupload = True
                wget = False
            elif 'uploadtext'+str(i) in postdata and postdata['uploadtext' + str(i)]:
                if 'uploadfilename'+str(i) in postdata and postdata['uploadfilename' + str(i)]:
                    filename = postdata['uploadfilename' + str(i)]
                else:
                    #if no filename exists, make a random one
                    filename =  "%032x" % random.getrandbits(128)
                output += "<upload seq=\""+str(i) +"\" filename=\""+postdata['uploadfilename' + str(i)] +"\">\n"

                archive = False
                filename = inputformat.filename(postdata['uploadfilename' + str(i)]) #set proper filename extension
                realupload = False
                wget = False
            elif 'uploadurl'+str(i) in postdata and postdata['uploadurl' + str(i)]:
                if 'uploadfilename'+str(i) in postdata and postdata['uploadfilename' + str(i)]:
                    #explicit filename passed
                    filename = postdata['uploadfilename' + str(i)]
                else:
                    #get filename from URL:
                    filename = os.path.basename(postdata['uploadurl' + str(i)])
                    if not filename:
                        filename =  "%032x" % random.getrandbits(128)  #make a random one

                output += "<upload seq=\""+str(i) +"\" filename=\""+postdata['uploadurl' + str(i)] +"\">\n"

                wget = True
                realupload = False
                filename = inputformat.filename(filename) #set proper filename extension


            inputformat = None
            for f in settings.INPUTFORMATS:                
                if f.__class__.__name__ == postdata['uploadformat' + str(i)]:
                    inputformat = f

            #write trigger so the system knows uploads are in progress
            #f = open(Project.path(project) + '.upload','w') 
            #f.close()

            printlog("Uploading '" + filename + "' (" + unicode(inputformat) + ", " + inputformat.encoding + ")")
            printdebug("(start copy upload)" )
            #upload file 
            #if archive:
            if inputformat.subdirectory:
                if not os.path.isdir(inputformat.subdirectory ):
                    os.mkdir(inputformat.subdirectory ) #TODO: make recursive and set mode
                filename = inputformat.subdirectory  + "/" + filename
    
            if wget:
                try:
                    req = urllib2.urlopen(postdata['uploadurl' + str(i)])
                except:
                    raise web.webapi.NotFound()
                CHUNK = 16 * 1024
                f = open(Project.path(project) + 'input/' + filename,'wb')
                while True:
                    chunk = req.read(CHUNK)
                    if not chunk: break
                    f.write(chunk)
            elif realupload:
                f = open(Project.path(project) + 'input/' + filename,'wb')
                for line in postdata['upload' + str(i)].file:
                    f.write(line) #encoding unaware, solves big-file upload problem?
            else:
                f = codecs.open(Project.path(project) + 'input/' + filename,'w', inputformat.encoding)
                f.write(postdata['uploadtext' + str(i)])
            f.close()
            printdebug("(end copy upload)" )

            #test uploaded files (this also takes care of extraction)
            output += self.test(project, filename, inputformat)
            
            output += "</upload>\n"

        output += "</clamupload>"

        #remove trigger
        #os.unlink(Project.path(project) + '.upload')

        #servicemodule = os.basename(sys.argv[0])[:-3]
    

        #cmd = ['upload.py', servicemodule, project] + args
        #process = subprocess.Popen(cmd, cwd=Project.path(project), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #if process:                
        #    f = open(Project.path(project) + '.upload','w') #TODO: check for problems with character encoding?
        #    f.write(str(process.pid))
        #    f.close()                                
        #    out, err = subprocess.communicate() # waits for process to finish
        #    #TODO: display output                	
        #else:
        #    raise web.webapi.InternalError("Unable to process upload package")                
            
        return output #200


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print >> sys.stderr, "Syntax: jobservice.py mysettingsmodule"
        sys.exit(1)
    settingsmodule = sys.argv[1]
    #if not settingsmodule.isalpha():  #security precaution
    #    print >> sys.stderr, "ERROR: Invalid service module specified!"
    #    sys.exit(1)
    #else:
    #import_string = "from " + settingsmodule + " import COMMAND, ROOT, URL, PARAMETERS, INPUTFORMATS, OUTPUTFORMATS, SYSTEM_ID, SYSTEM_NAME, SYSTEM_DESCRIPTION, USERS"
    import_string = "import " + settingsmodule + " as settings"
    exec import_string
    
    #remove first argument (web.py wants port in sys.argv[1]
    del sys.argv[1]

    if len(sys.argv) >= 2 and sys.argv[1] == '-d':
        DEBUG = True
        del sys.argv[1]

    #Check version
    if float(str(settings.REQUIRE_VERSION)[0:3]) < float(str(VERSION)[0:3]):
        print >> sys.stderr, "Version mismatch: at least " + str(settings.REQUIRE_VERSION) + " is required"
        sys.exit(1)   

    if not settings.ROOT[-1] == "/":
        settings.ROOT += "/" #append slash


    if 'PORT' in dir(settings):
        sys.argv.append(str(settings.PORT))       
   
    if not os.path.isdir(settings.ROOT):
        print >> sys.stderr, "Root directory does not exist yet, creating..."
        os.mkdir(settings.ROOT)
    if not os.path.isdir(settings.ROOT + 'corpora'):
        print >> sys.stderr, "Corpora directory does not exist yet, creating..."
        os.mkdir(settings.ROOT + 'corpora')
    if not os.path.isdir(settings.ROOT + 'projects'):
        print >> sys.stderr, "Projects directory does not exist yet, creating..."
        os.mkdir(settings.ROOT + 'projects')

    # Create decorator
    #requirelogin = real_requirelogin #fool python :) 
    #if USERS:
    #    requirelogin = digestauth.auth(lambda x: USERS[x], realm=SYSTEM_ID)
    if settings.USERS:
        auth = clam.common.digestauth.auth(userdb_lookup, realm= settings.SYSTEM_ID)
        

    JobService() #start
