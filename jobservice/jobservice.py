#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Jobservice --
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
       
STATUS_READY = 0
STATUS_RUNNING = 1
STATUS_DONE = 2
STATUS_UPLOAD = 10 #processing after upload
STATUS_DOWNLOAD = 11 #preparing before download

    

class JobService:
    clam_version = 0.1

    urls = (
    '/', 'Index',
    '/([A-Za-z0-9_]*)/', 'Project',
    '/([A-Za-z0-9_]*)/uplohousead', 'Uploader',
    '/([A-Za-z0-9_]*)/download', 'Downloader',
    '/([A-Za-z0-9_]*)/output/(.*)', 'FileHander',
    )

    def __init__(self):    
        self.service = web.application(self.urls, globals())
        self.service.internalerror = web.debugerror
        self.service.run()


        


    class Index(object):
        def GET(self):
            """Get list of projects"""
            global ROOT
            projects = []
            for f in glob.glob(ROOT + "projects/*"):
                if os.path.isdir(f):
                    projects.append(os.path.basename(f))
        render = web.template.render('templates')
        return render.index(projects)


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
        return render.inputformats(name, [ (format.__class__.name, format.name ) for format in INPUTFORMATS ])

    class Project(object):

        @staticmethod
        def path(project):
            """Get the path to the project (class method)"""
            global ROOT
            return ROOT + "projects/" + project + "/"

        def pid(self, project):
            pidfile = JobService.Project.path(project) + '.pid'
            if os.path.isfile(pidfile):
                f = open(pidfile,'r')
                pid = int(f.read(os.path.getfilesize(pidfile)))
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
                if os.path.isfile(JobService.Project.path(project) + ".pid"):
                    f = open(JobService.Project.path(project) + ".done",'w')
                    f.close()
                    os.path.remove(JobService.Project.path(project) + ".pid")
                return False        
     
        def abort(self,project):
            if self.pid(project) == 0:
                return False
            try:
                os.kill(self.pid, 15)
                os.path.remove(JobService.Project.path(project) + ".pid")
                return True
            except:
                return False  

        def done(self,project):
            return os.path.isfile(JobService.Project.path(project) + ".done")

        def preparingdownload(self,project):
            return os.path.isfile(JobService.Project.path(project) + ".download")

        def processingupload(self,project):
            return os.path.isfile(JobService.Project.path(project) + ".upload")

        def exists(self, project):
            """Check if the project exists"""
            return os.path.isdir(JobService.Project.path(project))

        def create(self, project):
            """create the project skeleton"""
            os.mkdir(JobService.Project.path(project))
            os.mkdir(JobService.Project.path(project) + 'input')
            os.mkdir(JobService.Project.path(project) + 'output')

            

        def status(self, project):
            global STATUS_READY, STATUS_RUNNING, STATUS_DONE, STATUS_DOWNLOAD, STATUS_UPLOAD
            pid = self.pid(project)
            if pid > 0 and self.running(pid):
                statusfile = JobService.Project.path(project) + ".status"
                if os.path.isfile(statusfile):
                    f = open(statusfile)
                    msg = f.read(os.path.getfilesize(statusfile))
                    f.close()
                    return (STATUS_RUNNING, msg)
                else:
                    return (STATUS_RUNNING,"The system is running") #running
            elif self.done():
                return (STATUS_DONE,"Done")
            elif self.preparingdownload():
                return (STATUS_DOWNLOAD,"Preparing package for download, please wait...")
            elif self.processingupload():
                return (STATUS_UPLOAD,"Processing upload, please wait...")
            else:
                return (STATUS_READY,"Ready to start")



        def outputindex(self,project, d = ''):        
            global OUTPUTFORMATS
            paths = []            
            for f in glob.glob(JobService.Project.path(project) + "output/" + d + "/*"):
                if os.path.isdir(f):
                    paths = paths + [ (d + "/" + x[0],x[1],x[2]) for x in self.dirindex(project,d+"/"+os.path.basename(f)) ]
                else:
                    filename = os.path.basename(f)
                    outputformat = Format() #unspecified format
                    for o in OUTPUTFORMATS:
                        if o.match(filename):
                            outputformat = o
                            break
                                    
                    paths.append( ( os.path.basename(f), outputformat.__class__.name, outputformat.encoding ) )
            return paths
                      

        def GET(self, project):
            """Main Get method: Get project state, parameters, outputindex"""
            global SYSTEM_ID, SYSTEM_NAME, PARAMETERS, STATUS_READY, STATUS_DONE
            if not self.exists(project):
                raise web.api.NotFound()
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
            render = web.template.render('templates')
            return render.response(SYSTEM_ID, SYSTEM_NAME, project, statuscode,statusmessage, PARAMETERS,corpora, outputpaths)


        def POST(self, project):
            global COMMAND, PARAMETERS
            
            if not self.exists(project):
                self.create(project)
                        
            #Generate arguments based on POSTed parameters
            args = []
            postdata = web.input()
            for parametergroup, parameters in PARAMETERS:
                for parameter in parameters:
                    if parameter.id in postdata:
                        parameter.set(postdata[parameter.id])
                        args.append(parameter.compileargs(parameter.value))
            
            #Start project with specified parameters
            cmd = [COMMAND] + args #call processing chain 
            process = subprocess.Popen(cmd,cwd=JobService.Project.path(project))				
            if process:
                pid = process.pid
                f = open(JobService.Project.path(project) + '.pid','w')
                f.write(str(pid))
                f.close()
                return "" #200
            else:
                raise web.webapi.InternalError("Unable to launch process")


        def DELETE(self, project):
            global STATUS_RUNNING
            if not self.exists(project):
                return web.api.NotFound()
            statuscode, _ = self.status(project)
            if statuscode == STATUS_RUNNING:
                self.abort(project)   
            shutil.rmtree(self.process.dir) #TODO: catch exception (won't work for symlinks)
            return "" #200

    class FileHandler(object):

        def GET(self,project, filename):    
            global OUTPUTFORMATS
            path = JobService.Project.path(project) + "output/" + filename.replace("..","")
            
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
            path = JobService.Project.path(project) + "output/" + project + ".tar.gz" 
            if not os.path.isfile(path):
                path = JobService.Project.path(project) + "output/" + project + ".tar.bz2" 
                if not os.path.isfile(path):            
                    path = JobService.Project.path(project) + "output/" + project + ".zip" 
                    if not os.path.isfile(path):            
                        raise web.webapi.NotFound() #No download file
            for line in open(path,'rb'): #TODO: check for problems with character encoding?
                yield line

        def POST(self):
            if not os.path.isfile(JobService.Project.path(project) + '.download'):
                postdata = web.input() 
                if 'format' in postdata:
                    format = postdata['format']
                else:
                    format = 'zip' #default          
                cmd = ['tools/make-download-package.sh', project] #call processing chain 
                process = subprocess.Popen(cmd, cwd=JobService.Project.path(project))	        			
                if process:
                    pid = process.pid
                    f = open(JobService.Project.path(project) + '.download','w') 
                    f.write(str(pid))
                    f.close()
                else:
                    raise web.webapi.InternalError("Unable to make download package")                
            return "" #200            
                
                

    class Uploader:

        def path(self, project):
            return JobService.Project.path() + 'input/'

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
                
            process = subprocess.Popen(cmd + " " + filename, cwd=self.path(project), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate() #waits for process to end 
    
            if namelist:
                for line in out:    
                    line = line.strip()        
                    if namelist == 'tar':
                        subfiles.append(line)
                    elif namelist == 'zip':
                        if line == 'inflating:': #NOTE: assumes unzip runs under english locale!
                            subfiles.append(line[10:]).strip()
            return [ subfile for subfile in subfiles if os.path.exists(self.path(project) + subfile) ] #return only the files that actually exist
           


        def test(self,project, filename, inputformat, depth = 0):
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
                    else:
                        o += " validated=\"no\" />\n"
                        remove = True #remove files that don't validate
                
                if self.isarchive(filename):            
                    for subfilename in self.extract(project,filename, inputformat):
                        self.test(subfilename, inputformat, depth + 1)
                    o += prefix + "</file>\n"    

            if remove:
                os.unlink(self.path(project) + filename)
    
            return o


        def GET(self, project):
            #should use template instead
            return '<html><head></head><body><form method="POST" enctype="multipart/form-data" action=""><input type="hidden" name="uploadcount" value="1"><input type="file" name="upload1" /><br />' + JobService.inputformats('uploadformat1') + '<br/><input type="submit" /></form></body></html>'

        def POST(self, project):
            global INPUTFORMATS
            postdata = web.input(corpus={})
            if not 'uploadcount' in postdata or not postdata['uploadcount'].isdigit():
                raise web.webapi.BadRequest('No valid uploadcount specified') #TODO: verify this works
                        
  

            #Check if all uploads have a valid format specified, raise 403 otherwise, dismissing any uploads
            for i in range(1,int(postdata['uploadcount']) + 1):
                if 'upload'+str(i) in postdata:
                    inputformat = None
                    for f in INPUTFORMATS:                
                        if f.__class__.name == postdata['uploadformat' + str(i)]:
                            inputformat = f
                
                    if not inputformat:
                        raise web.forbidden() 
                else:
                    raise web.forbidden()


            output = "<clamupload uploads=\""+str(postdata['uploadcount'])+"\">\n"

            #we may now assume all upload-data exists:
            for i in range(1,int(postdata['uploadcount']) + 1):
                output = "<upload seq=\""+str(i) +"\" filename=\""+postdata['upload' + str(i)].filename +"\">\n"

                inputformat = None
                for f in INPUTFORMATS:                
                    if f.__class__.name == postdata['uploadformat' + str(i)]:
                        inputformat = f

                filename = postdata['corpus'].filename.lower()

                #Is the upload an archive?
                extension = postdata['upload' + str(i)].split(".")[-1]
                if extension == "gz" or  extension == "bz2" or extension == "tar" or  extension == "zip":
                    archive = True
                else:                
                    #upload not an archive:
                    archive = False
                    filename = inputformat.filename(postdata['corpus'].filename) #set proper filename extension

                #write trigger so the system knows uploads are in progress
                #f = open(JobService.Project.path(project) + '.upload','w') 
                #f.close()

                #upload file 
                if archive:
                    f = open(JobService.Project.path(project) + 'input/' + filename,'w') #TODO: check for problems with character encoding?
                else:
                    f = codecs.open(JobService.Project.path(project) + 'input/' + filename,'w', inputformat.encoding)
                for line in postdata['corpus'].file:
                    f.write(line)
                f.close()

                #test uploaded files
                output += self.test(project, filename, inputformat)
                
                output += "</upload>\n"

            output += "</clamupload>"

            #remove trigger
            #os.unlink(JobService.Project.path(project) + '.upload')

            #servicemodule = os.basename(sys.argv[0])[:-3]
       

            #cmd = ['upload.py', servicemodule, project] + args
            #process = subprocess.Popen(cmd, cwd=JobService.Project.path(project), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #if process:                
            #    f = open(JobService.Project.path(project) + '.upload','w') #TODO: check for problems with character encoding?
            #    f.write(str(process.pid))
            #    f.close()                                
            #    out, err = subprocess.communicate() # waits for process to finish
            #    #TODO: display output                	
            #else:
            #    raise web.webapi.InternalError("Unable to process upload package")                
                
            return output #200
