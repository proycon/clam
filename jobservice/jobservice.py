#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Jobservice --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompelcp jobservice.py /tmp/sources/clam/jobservice/
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
from parameters import *
from formats import *
       
STATUS_READY = 0
STATUS_RUNNING = 1
STATUS_DONE = 2
STATUS_UPLOAD = 10 #processing after upload
STATUS_DOWNLOAD = 11 #preparing before download


DEBUG = False
    
#Empty defaults
SYSTEM_ID = "clam"
SYSTEM_NAME = "CLAM: Computional Linguistics Application Mediator"
SYSTEM_DESCRIPTION = "CLAM is a webservice wrapper around NLP tools"
COMMAND = ""
ROOT = "."
PARAMETERS = []
INPUTFORMATS = []
OUTPUTFORMATS = []
URL = "http://localhost:8080"


def printlog(msg):
    now = datetime.datetime.now()
    print "------------------- [" + now.strftime("%d/%b/%Y %H:%M:%S") + "] " + msg 

def printdebug(msg):
    global DEBUG
    if DEBUG: printlog("DEBUG: " + msg)
        
class JobService:
    clam_version = 0.1

    urls = (
    '/', 'Index',
    '/([A-Za-z0-9_]*)/?', 'Project',
    '/([A-Za-z0-9_]*)/upload/?', 'Uploader',
    '/([A-Za-z0-9_]*)/download/?', 'Downloader',
    '/([A-Za-z0-9_]*)/output/(.*)', 'FileHander',
    )

    def __init__(self):    
        global COMMAND,ROOT, PARAMETERS, INPUTFORMATS, OUTPUTFORMATS
        printlog("Starting CLAM JobService, version " + str(self.clam_version) + " ...")
        if not ROOT or not os.path.isdir(ROOT):
            print >>sys.stderr,"ERROR: Specified root path " + ROOT + " not found"                 
            sys.exit(1)
        elif not COMMAND or os.system("which " + COMMAND + "> /dev/null 2> /dev/null") != 0:
            print >>sys.stderr,"ERROR: Specified command " + COMMAND + " not found"                 
            sys.exit(1)            
        #elif not INPUTFORMATS:
        #    print >>sys.stderr,"ERROR: No inputformats specified!"
        #    sys.exit(1)            
        #elif not OUTPUTFORMATS:
        #    print >>sys.stderr,"ERROR: No outputformats specified!"
        #    sys.exit(1)            
        elif not PARAMETERS:
            print >>sys.stderr,"WARNING: No parameters specified in settings module!"
        else:            
            try:
                for parametergroup, parameters in PARAMETERS:
                    for parameter in parameters:
                        assert isinstance(parameter,AbstractParameter)
            except:
                print >>sys.stderr,"ERROR: Syntax error in parameter specification"
                sys.exit(1)            
            
        self.service = web.application(self.urls, globals())
        self.service.internalerror = web.debugerror
        self.service.run()

    @staticmethod
    def corpusindex(): 
            """Get list of pre-installed corpora"""
            global ROOT
            corpora = []
            for f in glob.glob(ROOT + "corpora/*"):
                if os.path.isdir(f):
                    corpora.append(os.path.basename(f))
            return corpora

    @staticmethod
    def inputformats(name="inputformat"):
        """Renders a list of input formats"""
        #MAYBE TODO: add selected?
        global INPUTFORMATS
        render = web.template.render('templates')
        return render.inputformats(name, [ (format.__class__.__name__, format.name ) for format in INPUTFORMATS ])
    


class Index(object):
    def GET(self):
        """Get list of projects"""
        global ROOT, URL, SYSTEM_ID, SYSTEM_NAME
        projects = []
        for f in glob.glob(ROOT + "projects/*"):
            if os.path.isdir(f):
                projects.append(os.path.basename(f))
        render = web.template.render('templates')
        return render.index(SYSTEM_ID, SYSTEM_NAME, URL, projects)
        


class Project(object):

    @staticmethod
    def path(project):
        """Get the path to the project (static method)"""
        global ROOT
        return ROOT + "projects/" + project + "/"

    @staticmethod
    def create(project):         
        """Create project skeleton if it does not already exist (static method)"""
        global ROOT
        if not os.path.isdir(ROOT + "projects/" + project):
            printlog("Creating project '" + project + "'")
            os.mkdir(ROOT + "projects/" + project)
            os.mkdir(ROOT + "projects/" + project + "/input")
            os.mkdir(ROOT + "projects/" + project + "/output")

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
        if self.pid(project) == 0:
            return False
        try:
            os.kill(self.pid, 0) #(doesn't really kill, but throws exception when process does not exist)
            return True
        except:
            if os.path.isfile(Project.path(project) + ".pid"):
                f = open(Project.path(project) + ".done",'w')
                f.close()
                os.path.remove(Project.path(project) + ".pid")
            return False        
    
    def abort(self,project):
        if self.pid(project) == 0:
            return False
        try:
            printlog("Aborting process in project '" + project + "'" )
            os.kill(self.pid, 15)
            os.path.remove(Project.path(project) + ".pid")
            return True
        except:
            return False  

    def done(self,project):
        return os.path.isfile(Project.path(project) + ".done")

    def preparingdownload(self,project):
        return os.path.isfile(Project.path(project) + ".download")

    def processingupload(self,project):
        return os.path.isfile(Project.path(project) + ".upload")

    def exists(self, project):
        """Check if the project exists"""
        return os.path.isdir(Project.path(project))


    def status(self, project):
        global STATUS_READY, STATUS_RUNNING, STATUS_DONE, STATUS_DOWNLOAD, STATUS_UPLOAD
        pid = self.pid(project)
        if pid > 0 and self.running(pid):
            statusfile = Project.path(project) + ".status"
            if os.path.isfile(statusfile):
                f = open(statusfile)
                msg = f.read(os.path.getsize(statusfile))
                f.close()
                return (STATUS_RUNNING, msg)
            else:
                return (STATUS_RUNNING, "The system is running") #running
        elif self.done(project):
            return (STATUS_DONE, "Done")
        elif self.preparingdownload(project):
            return (STATUS_DOWNLOAD, "Preparing package for download, please wait...")
        elif self.processingupload(project):
            return (STATUS_UPLOAD, "Processing upload, please wait...")
        else:
            return (STATUS_READY, "Ready to start")


    def dirindex(self, project, formats, mode = 'output', d = ''):
        paths = []            
        for f in glob.glob(Project.path(project) + mode + "/" + d + "/*"):
            if os.path.isdir(f):
                paths = paths + [ (d + "/" + x[0],x[1],x[2]) for x in self.dirindex(project,formats, mode, d+"/"+os.path.basename(f)) ]
            else:
                filename = os.path.basename(f)
                format = Format() #unspecified format
                for fmt in formats:
                    if fmt.match(filename):
                        format = fmt
                        break                                
                paths.append( ( os.path.basename(f), format.__class__.__name__, format.encoding ) )
        return paths

    def inputindex(self,project):        
        global INPUTFORMATS
        return self.dirindex(project,INPUTFORMATS,'input')



    def outputindex(self,project, d = ''):        
        global OUTPUTFORMATS
        return self.dirindex(project,OUTPUTFORMATS,'output')
                    

    def GET(self, project):
        """Main Get method: Get project state, parameters, outputindex"""
        global SYSTEM_ID, SYSTEM_NAME, PARAMETERS, STATUS_READY, STATUS_DONE, OUTPUTFORMATS, INPUTFORMATS, URL
        if not self.exists(project):
            raise web.webapi.NotFound()
        statuscode, statusmsg = self.status(project)
        corpora = []
        if statuscode == STATUS_READY:
            corpora = JobService.corpusindex()
        else:
            corpora = []
        if statuscode == STATUS_DONE:
            outputpaths = self.outputindex(project)
        else:
            outputpaths = []        
        if statuscode == STATUS_READY:
            inputpaths = self.inputindex(project)
        else:
            inputpaths = []      
        #check if there are invalid parameters:
        errors = "no"
        errormsg = ""
        for parametergroup, parameters in PARAMETERS:
            for parameter in parameters:
                if parameter.error:
                    errors = "yes"
                    errormsg = "One or more parameters are invalid"
                    break
        render = web.template.render('templates')
        return render.response(SYSTEM_ID, SYSTEM_NAME, project, URL, statuscode,statusmsg, errors, errormsg, PARAMETERS,corpora, outputpaths,inputpaths, OUTPUTFORMATS, INPUTFORMATS )

    def PUT(self, project):
        """Create an empty project"""
        Project.create(project)
        return "" #200

    def POST(self, project):
        global COMMAND, PARAMETERS
        

        Project.create(project)
                    
        #Generate arguments based on POSTed parameters
        params = []
        postdata = web.input()
        errors = False
        for parametergroup, parameters in PARAMETERS:
            for parameter in parameters:
                if parameter.id in postdata:
                    if parameter.set(postdata[parameter.id]): #may generate an error in parameter.error
                        params.append(parameter.compileargs(parameter.value))
                    else:
                        errors = True
                elif parameter.required:
                    #Not all required parameters were filled!
                    errors = True

        if errors:
            #There are parameter errors, return 200 (OK) response, but with error data so it can be corrected
            #TODO: send a custom 400 (bad request) instead of 200, but with same content as GET!
            return self.GET(project)
        else:
            #Start project with specified parameters
            cmd = COMMAND
            cmd.replace('$PARAMETERS', " ".join(params))
            if 'usecorpus' in postdata and postdata['usecorpus']:
                corpus = postdata['usecorpus'].replace('..','') #security            
                #use a preinstalled corpus:
                if os.path.exists(ROOT + "corpora/" + corpus):
                    cmd.replace('$INPUTDIRECTORY', Project.path(project) + 'input/')
                else:
                    raise web.webapi.NotFound("Corpus " + corpus + " not found") #TODO: Verify custom not-found messages work?
            else:
                cmd.replace('$INPUTDIRECTORY', Project.path(project) + 'input/')
            cmd.replace('$OUTPUTDIRECTORY',Project.path(project) + 'output/')
            #cmd = sum([ params if x == "$PARAMETERS" else [x] for x in COMMAND ] ),[])
            #cmd = sum([ Project.path(project) + 'input/' if x == "$INPUTDIRECTORY" else [x] for x in COMMAND ] ),[])        
            #cmd = sum([ Project.path(project) + 'output/' if x == "$OUTPUTDIRECTORY" else [x] for x in COMMAND ] ),[])        
            #TODO: protect against insertion
            printlog("Starting " + COMMAND + ": " + repr(cmd) + " ..." )
            process = subprocess.Popen(cmd,cwd=Project.path(project), shell=True)				
            if process:
                pid = process.pid
                printlog("Started with pid " + str(pid) )
                f = open(Project.path(project) + '.pid','w')
                f.write(str(pid))
                f.close()
                return self.GET(project) #return 200 -> GET
            else:
                raise web.webapi.InternalError("Unable to launch process")


    def DELETE(self, project):
        global STATUS_RUNNING
        if not self.exists(project):
            return web.webapi.NotFound()
        statuscode, _ = self.status(project)
        if statuscode == STATUS_RUNNING:
            self.abort(project)   
        printlog("Deleting project '" + project + "'" )
        shutil.rmtree(Project.path(project))
        return "" #200

class FileHandler(object):

    def GET(self,project, filename):    
        global OUTPUTFORMATS
        path = Project.path(project) + "output/" + filename.replace("..","")
        
        #TODO: find outputformat?

        if os.path.isfile(path): 
            for line in open(path,'r'): #TODO: check for problems with character encoding?
                yield line
        elif os.path.isdir(path): 
            for f in glob.glob(path + "/*"):
                yield os.path.basename(f)                
        else:
            raise web.webapi.NotFound()


class Downloader:
        
    def GET(self):
        path = Project.path(project) + "output/" + project + ".tar.gz" 
        if not os.path.isfile(path):
            path = Project.path(project) + "output/" + project + ".tar.bz2" 
            if not os.path.isfile(path):            
                path = Project.path(project) + "output/" + project + ".zip" 
                if not os.path.isfile(path):            
                    raise web.webapi.NotFound() #No download file
        for line in open(path,'rb'): #TODO: check for problems with character encoding?
            yield line

    def POST(self):
        if not os.path.isfile(Project.path(project) + '.download'):
            postdata = web.input() 
            if 'format' in postdata:
                format = postdata['format']
            else:
                format = 'zip' #default          
            cmd = ['tools/make-download-package.sh', project] #call processing chain 
            process = subprocess.Popen(cmd, cwd=Project.path(project))	        			
            if process:
                pid = process.pid
                f = open(Project.path(project) + '.download','w') 
                f.write(str(pid))
                f.close()
            else:
                raise web.webapi.InternalError("Unable to make download package")                
        return "" #200            
            
            

class Uploader:

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
                if inputformat.validate(self.path(project) + filename):
                    o += " validated=\"yes\" />\n"
                    printlog("Succesfully validated '" + filename + "'" )
                else:
                    o += " validated=\"no\" />\n"
                    printlog("File did not validate '" + filename + "'" )
                    remove = True #remove files that don't validate
            
            if self.isarchive(filename):            
                for subfilename in self.extract(project,filename, inputformat):
                    printdebug("Extracted from archive: " + subfilename)
                    o += self.test(project,subfilename, inputformat, depth + 1)
                o += prefix + "</file>\n"    

        if remove and os.path.exists(self.path(project) + filename):
           printdebug("Removing '" + filename + "'" )
           os.unlink(self.path(project) + filename)

        return o


    def GET(self, project):
        #should use template instead
        return '<html><head></head><body><form method="POST" enctype="multipart/form-data" action=""><input type="hidden" name="uploadcount" value="1"><input type="file" name="upload1" /><br />' + str(JobService.inputformats('uploadformat1')) + '<br/><input type="submit" /></form></body></html>'

    def POST(self, project):
        global INPUTFORMATS, URL

        #postdata = web.input()

        #defaults (max 25 uploads)
        kwargs = {}
        for i in range(1,26):    
            kwargs['upload' + str(i)] = {}                            
        postdata = web.input(**kwargs)
        if not 'uploadcount' in postdata or not postdata['uploadcount'].isdigit():
            raise web.webapi.BadRequest('No valid uploadcount specified') #TODO: verify this works
        if int(postdata['uploadcount']) > 25:
            raise web.webapi.BadRequest('Too many uploads') #TODO: verify this works

        #Check if all uploads have a valid format specified, raise 403 otherwise, dismissing any uploads
        for i in range(1,int(postdata['uploadcount']) + 1):
            if 'upload'+str(i) in postdata or ('uploadfilename'+str(i) in postdata and 'uploadtext' + str(i) in postdata):
                inputformat = None
                for f in INPUTFORMATS:                
                    if f.__class__.__name__ == postdata['uploadformat' + str(i)]:
                        inputformat = f
            
                if not inputformat:
                    raise web.forbidden() 
            else:
                raise web.forbidden()

        Project.create(project)

        output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        output += "<?xml-stylesheet type=\"text/xsl\" href=\"" + URL + "/static/interface.xsl\"?>"
        output += "<clamupload uploads=\""+str(postdata['uploadcount'])+"\">\n"

        #we may now assume all upload-data exists:
        for i in range(1,int(postdata['uploadcount']) + 1):
            if 'upload'+str(i) in postdata and (not 'uploadtext'+str(i) in postdata or not postdata['uploadtext' + str(i)]):
                output += "<upload seq=\""+str(i) +"\" filename=\""+postdata['upload' + str(i)].filename +"\">\n"

                filename = postdata['upload' + str(i)].filename.lower()

                #Is the upload an archive?
                extension = filename.split(".")[-1]
                if extension == "gz" or  extension == "bz2" or extension == "tar" or  extension == "zip":
                    archive = True
                else:                
                    #upload not an archive:
                    archive = False
                    filename = inputformat.filename(filename) #set proper filename extension
                realupload = True
            elif 'uploadtext'+str(i) in postdata and postdata['uploadtext' + str(i)] and 'uploadfilename'+str(i) in postdata and postdata['uploadfilename' + str(i)]:
                archive = False
                filename = inputformat.filename(postdata['uploadfilename' + str(i)]) #set proper filename extension
                realupload = False
    

            inputformat = None
            for f in INPUTFORMATS:                
                if f.__class__.__name__ == postdata['uploadformat' + str(i)]:
                    inputformat = f

            #write trigger so the system knows uploads are in progress
            #f = open(Project.path(project) + '.upload','w') 
            #f.close()

            printlog("Uploading '" + filename + "'" )
            printdebug("(start copy upload)" )
            #upload file 
            if archive:
                f = open(Project.path(project) + 'input/' + filename,'wb')
            else:
                f = codecs.open(Project.path(project) + 'input/' + filename,'w', inputformat.encoding)
            if realupload:
                for line in postdata['upload' + str(i)].file:
                    f.write(line)
            else:
                f.write(postdata['uploadtext' + str(i)])
            f.close()
            printdebug("(end copy upload)" )

            #test uploaded files
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


#class Interface:
#    """Dynamically(!) generates the XSL to render the XML response"""
#    def GET(self, project):
#        global INPUTFORMATS, PARAMETERS
#        render = web.template.render('interface')   
#        parameterclasses = []
#        for parametergroup, parameters in PARAMETERS:
#            for parameter in parameters:
#                if not parameter.__class__ in parameterclasses:
#                    parameterclasses.append(parameter.__class__)
#        return render.response(parameterclasses, JobService.inputformats('uploadformat1'))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print >> sys.stderr, "Syntax: jobservice.py mysettingsmodule [port]"
        sys.exit(1)
    settingsmodule = sys.argv[1]
    if not settingsmodule.isalpha():  #security precaution
        print >> sys.stderr, "ERROR: Invalid service module specified!"
        sys.exit(1)
    else:
        import_string = "from " + settingsmodule + " import COMMAND, ROOT, URL, PARAMETERS, INPUTFORMATS, OUTPUTFORMATS, SYSTEM_ID, SYSTEM_NAME, SYSTEM_DESCRIPTION"
        exec import_string
    
    #remove first argument (web.py wants port in sys.argv[1]
    del sys.argv[1]

    if len(sys.argv) >= 2 and sys.argv[1] == '-d':
        DEBUG = True
        del sys.argv[1]

    JobService() #start
