#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Client --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/clam
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

import codecs
import os.path
#import httplib2
import urllib2
from urllib import urlencode
from lxml import etree as ElementTree
from StringIO import StringIO

from clam.external.poster.encode import multipart_encode
from clam.external.poster.streaminghttp import register_openers



import clam.common.status
import clam.common.parameters
import clam.common.formats
from clam.common.data import CLAMData, CLAMFile, CLAMInputFile, CLAMOutputFile, CLAMMetaData, InputTemplate, OutputTemplate, VERSION as DATAAPIVERSION
from clam.common.util import RequestWithMethod

VERSION = '0.7.7'
if VERSION != DATAAPIVERSION:
    raise Exception("Version mismatch beween Client API ("+clam.common.data.VERSION+") and Data API ("+DATAAPIVERSION+")!")

# Register poster's streaming http handlers with urllib2
register_openers()


class BadRequest(Exception):
     def __init__(self):
        pass
     def __str__(self):
        return "Bad Request"

class NotFound(Exception):
    """Raised on 404 - Not Found Errors"""
    def __init__(self, msg=""):
        self.msg = msg
    def __str__(self):
        return "Not Found: " +  self.msg

class PermissionDenied(Exception):
    """Raised on 403 - Permission Denied Errors (but only if no CLAM XML response is provided)"""
    def __init__(self, msg = ""):
        self.msg = msg
    def __str__(self):
        if isinstance(clam.common.data,CLAMData):
            return "Permission Denied"
        else:
            return "Permission Denied: " + self.msg

class ServerError(Exception):
    """Raised on 500 - Internal Server Error. Indicates that something went wrong on the server side."""
    def __init__(self, msg = ""):
        self.msg = msg
    def __str__(self):
        return "Server Error: " + self.msg

class AuthRequired(Exception):
    """Raised on 401 - Authentication Required error. Service requires authentication, pass user credentials in CLAMClient constructor."""
    def __init__(self, msg = ""):
        self.msg = msg            
    def __str__(self):
        return "Authorization Required: " + self.msg

class NoConnection(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "Can't establish a connection with the server" 


class UploadError(Exception):
    def __init__(self, msg = ""):
        self.msg = msg            
    def __str__(self):
        return "Error during Upload: " + self.msg

class ParameterError(Exception):
    """Raised on Parameter Errors, i.e. when a parameter does not validate, is missing, or is otherwise set incorrectly."""
    def __init__(self, msg = ""):
        self.msg = msg            
    def __str__(self):
        return "Error setting parameter: " + self.msg

class TimeOut(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "Connection with server timed-out" 
        

class CLAMClient:
    def __init__(self, url, user=None, password=None):
        """Initialise the CLAM client (does not actually connect yet)
        
        url - URL of the webservice
        user - username (or None)
        realm - authentication realm
        password - password (or None)
        """
        
        #self.http = httplib2.Http()
        if url[-1] != '/': url += '/'
        self.url = url
        if user and password:
            self.authenticated = True
            #for most things we use httplib2
            #self.http.add_credentials(user, password)
            
            #for file upload we use urllib2:
            self.passman = urllib2.HTTPPasswordMgrWithDefaultRealm() 
            # this creates a password manager
            self.passman.add_password(None, url, user, password) #realm will be automagically detected
            authhandler = urllib2.HTTPDigestAuthHandler(self.passman)
            opener = urllib2.build_opener(authhandler)
            opener.addheaders = [('User-agent', 'CLAMClientAPI-' + VERSION)]
            urllib2.install_opener(opener)
        else:
            self.authenticated = False
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'CLAMClientAPI-' + VERSION)]
            urllib2.install_opener(opener)
    
    
    def request(self, url='', method = 'GET', data = None):        
        if data: 
            request = RequestWithMethod(self.url + url,data,method=method)
        else:
            request = RequestWithMethod(self.url + url,method=method)
        try:
            response = urllib2.urlopen(request)            
        except Exception, e:
            try:
                statuscode = int(e.code)
            except AttributeError:
                raise e    
                
            if statuscode >= 200 and statuscode < 300:
                #this is no error!
                return self._parse(e.read())  
            elif statuscode == 400:
                raise BadRequest()
            elif statuscode == 401:
                raise AuthRequired()
            elif statuscode == 403:        
                content = e.read()
                data = self._parse(content)
                if data:
                    raise PermissionDenied(data)
                else:
                    raise PermissionDenied(content)
            elif statuscode == 404 and data:
                raise NotFound(e.read())
            elif statuscode == 500:
                raise ServerError(e.read())
            elif statuscode == 405:
                raise ServerError("Server returned 405: Method not allowed for " + method + " on " + self.url + url)                
            elif statuscode == 408:
                raise TimeOut()            
            else:
                raise
      
        return self._parse(response.read())        
    
            
    def _request_httplib2(self, url, method = 'GET', data = None): #old, obsolete
        """Returns a CLAMData object if a proper CLAM XML response is received. Otherwise: returns True, on success, False on failure.  Raises an Exception on most HTTP errors!"""

        try:
            if data: 
                response, content = self.http.request(self.url + url, method, data)
            else:
                response, content = self.http.request(self.url + url, method)
        except:
            raise NoConnection()
        try:
            return self._parse(response, content)
        except TimeOut:
            #Do it again once
            try:
                if data: 
                    response, content = self.http.request(self.url + url, method, data)
                else:
                    response, content = self.http.request(self.url + url, method)
                return self._parse(response, content)                    
            except:
                raise
        except:
            raise    

    def _parse(self, content):    
        if content.find('<clam') != -1:
            data = CLAMData(content)
            if data.errors:
                error = data.parametererror()
                if error:
                    raise ParameterError(error)
            return data
        else:
            return True

    def _parse_old(self, response, content):    
        if content.find('<clam') != -1:
            data = CLAMData(content)
            if data.errors:
                error = data.parametererror()
                if error:
                    raise ParameterError(error)
        else:
            data = False
            
        if response['status'] == '200' or response['status'] == '201' or response['status'] == '202':
            if not data: data = True
        elif response['status'] == '400':
            raise BadRequest()
        elif response['status'] == '401':
            raise AuthRequired()
        elif response['status'] == '403' and data:
            raise PermissionDenied(data)
        elif response['status'] == '404' and data:
            raise NotFound(content)
        elif response['status'] == '500':
            raise ServerError(data)
        elif response['status'] == '408':
            raise TimeOut()
        else:            
            raise Exception("Server returned HTTP response " + response['status'])
        
        return data
                
   

 
    def index(self):
        """Get index of projects. Returns CLAMData instance. Use CLAMData.projects for the index of projects."""
        return self.request('')

    def get(self, project):
        """Query the project status. Returns CLAMData instance."""
        try:
            data = self.request(project + '/')
        except:
            raise
        if not isinstance(data, CLAMData):
            raise Exception("Unable to retrieve CLAM Data")
        else:
            return data
            

    def create(self,project):
        """Create a new project"""
        return self.request(project + '/', 'PUT')
    

    def start(self, project, **parameters):
        """Start a run. 'project' is the ID of the project, and **parameters are keyword arguments for
        the global parameters. Returns a CLAMData object or raises exceptions. Note that no exceptions are raised on parameter errors, you have to check for those manually! (Use startsafe instead if want Exceptions on parameter errors)"""
        auth = None
        if 'auth' in parameters:
            auth = parameters['auth']
            del parameters['auth']

        return self.request(project + '/', 'POST', urlencode(parameters))        
        
    def startsafe(self, project, **parameters):
        """Start a run. 'project' is the ID of the project, and **parameters are keyword arguments for
        the global parameters. Returns a CLAMData object or raises exceptions. This version, unlike start(), raises Exceptions (ParameterError) on parameter errors"""
        
        try:
            data = self.start(project, **parameters)
            for parametergroup, paramlist in data.parameters:
                for parameter in paramlist:
                    if parameter.error:
                        raise ParameterError(parameter.error)
            return data
        except:
            raise
        

    def delete(self,project):
        """aborts AND deletes a project"""
        return self.request(project + '/', 'DELETE')

    def abort(self, project): #alias
        """aborts AND deletes a project (alias of delete() )"""    
        return self.abort(project)


    def downloadarchive(self, project, targetfile, format = 'zip'):
        """Download all output files as a single archive
        
        format - the format of the archive, can be 'zip','gz','bz2'
        
        """
        #TODO: Redo
        req = urllib2.urlopen(self.url + project + '/output/?format=' + format) #TODO: Auth support
        CHUNK = 16 * 1024
        while True:
            chunk = req.read(CHUNK)
            if not chunk: break
            targetfile.write(chunk)


    def getinputfilename(self, inputtemplate, filename):        
        """Determine the final filename for an input file given an inputtemplate and a given filename. """
        if inputtemplate.filename:
            filename = inputtemplate.filename
        elif inputtemplate.extension: 
            if filename.lower()[-4:] == '.zip' or filename.lower()[-7:] == '.tar.gz' or filename.lower()[-8:] == '.tar.bz2':
                #pass archives as-is
                return filename
                
            if filename[-len(inputtemplate.extension) - 1:].lower() != '.' +  inputtemplate.extension.lower():
                filename += '.' + inputtemplate.extension        
                
        return filename

    def _parseupload(self, node):
        if not isinstance(node,ElementTree._Element):
            try:
                node = ElementTree.parse(StringIO(node)).getroot() 
            except:
                raise Exception(node)
        if node.tag != 'clamupload':
            raise Exception("Not a valid CLAM upload response")
        for node in node:
            if node.tag == 'upload':
                for subnode in node:
                    if subnode.tag == 'error':
                        raise UploadError(subnode.text)
                    if subnode.tag == 'parameters':           
                        if 'errors' in subnode.attrib and subnode.attrib['errors'] == 'yes':                    
                            errormsg = "The submitted metadata did not validate properly" #default
                            for parameternode in subnode:                    
                                if 'error' in parameternode.attrib:
                                    errormsg = parameternode.attrib['error']
                                    raise ParameterError(errormsg + " (parameter="+parameternode.attrib['id']+")")
                            raise ParameterError(errormsg)
        return True


    def addinputfile(self, project, inputtemplate, sourcefile, **kwargs):
        """Add/upload an input file to the CLAM service.
        
        project - the ID of the project you want to add the file to.
        inputtemplate - The input template you want to use to add this file (InputTemplate instance)
        sourcefile - The file you want to add: either an instance of 'file' or a string containing a filename 
        
        Keyword arguments (optional but recommended!):
            filename - the filename on the server (will be same as sourcefile if not specified)
            metadata - A metadata object.
            metafile - A metadata file (filename)
            Any other keyword arguments will be passed as metadata and matched with the input template's parameters.
        """
        if isinstance( inputtemplate, str) or isinstance( inputtemplate, unicode):
            data = self.get(project) #causes an extra query to server
            inputtemplate = data.inputtemplate(inputtemplate)
        elif not isinstance(inputtemplate, InputTemplate):
            raise Exception("inputtemplate must be instance of InputTemplate. Get from CLAMData.inputtemplate(id)")
        
        if not isinstance(sourcefile, file):
            sourcefile = open(sourcefile,'r')
        
        if 'filename' in kwargs:            
            filename = self.getinputfilename(inputtemplate, kwargs['filename'])            
        else:
            filename = self.getinputfilename(inputtemplate, os.path.basename(sourcefile.name) )
                    
        data = {"file": sourcefile, 'inputtemplate': inputtemplate.id}
        for key, value in kwargs.items():
            if key == 'filename':
                pass #nothing to do
            elif key == 'metadata':
                assert isinstance(value, CLAMMetaData)
                data['metadata'] =  value.xml()
            elif key == 'metafile':
                data['metafile'] = open(value,'r')
            else:
                data[key] = value
        
        opener = register_openers()
        opener.addheaders = [('User-agent', 'CLAMClientAPI-' + VERSION)]
        if self.authenticated:
            opener.add_handler( urllib2.HTTPDigestAuthHandler(self.passman) )
        datagen, headers = multipart_encode(data)
                
        # Create the Request object
        request = urllib2.Request(self.url + project + '/input/' + filename, datagen, headers)
        try:
            xml = urllib2.urlopen(request).read()
        except urllib2.HTTPError, e:
            xml = e.read()        
        
        try:
            return self._parseupload(xml)
        except:
            raise
        

    def addinput(self, project, inputtemplate, contents, **kwargs):
        """Add an input file to the CLAM service. Explictly providing the contents as a string
                
        project - the ID of the project you want to add the file to.
        inputtemplate - The input template you want to use to add this file (InputTemplate instance)
        contents - The contents for the file to add (string)
        
        Keyword arguments (optional but recommended!):
            filename - the filename on the server (mandatory!)
            metadata - A metadata object.
            metafile - A metadata file (filename)
            Any other keyword arguments will be passed as metadata and matched with the input template's parameters.
        """
        if isinstance( inputtemplate, str) or isinstance( inputtemplate, unicode):
            data = self.get(project) #causes an extra query to server
            inputtemplate = data.inputtemplate(inputtemplate)
        elif not isinstance(inputtemplate, InputTemplate):
            raise Exception("inputtemplate must be instance of InputTemplate. Get from CLAMData.inputtemplate(id)")
        
        
        if 'filename' in kwargs:
            filename = self.getinputfilename(inputtemplate, kwargs['filename'])
        else:
            raise Exception("No filename provided!")
                    
        data = {"contents": contents, 'inputtemplate': inputtemplate.id}
        for key, value in kwargs.items():
            if key == 'filename':
                pass #nothing to do
            elif key == 'metadata':
                assert isinstance(value, CLAMMetaData)
                data['metadata'] =  value.xml()
            elif key == 'metafile':
                data['metafile'] = open(value,'r')
            else:
                data[key] = value
        
                
        opener = register_openers()
        opener.addheaders = [('User-agent', 'CLAMClientAPI-' + VERSION)]
        if self.authenticated:
            opener.add_handler( urllib2.HTTPDigestAuthHandler(self.passman) )
        datagen, headers = multipart_encode(data)
        
        # Create the Request object
        request = urllib2.Request(self.url + project + '/input/' + filename, datagen, headers)
        try:
            xml = urllib2.urlopen(request).read()
        except urllib2.HTTPError, e:
            xml = e.read()        
        try:
            return self._parseupload(xml)
        except:
            raise
                


    def upload(self,project, inputtemplate, sourcefile, **kwargs):
        """Alias for addinputfile."""
        return self.addinputfile(project, inputtemplate,sourcefile, **kwargs)

