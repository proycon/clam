#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Data API  --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#
#       Centre for Language and Speech Technology / Language Machines
#       Radboud University Nijmegen
#
#       Licensed under GPLv3
#
###############################################################

#pylint: disable=wrong-import-order

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import requests
import os.path
import io
import json
import time
import re
import yaml
from copy import copy
from lxml import etree as ElementTree
if sys.version < '3':
    from StringIO import StringIO #pylint: disable=import-error
else:
    from io import StringIO, BytesIO #pylint: disable=ungrouped-imports
import clam.common.parameters
import clam.common.status
import clam.common.util
import clam.common.viewers

VERSION = '2.4.6'

#dirs for services shipped with CLAM itself
CONFIGDIR = os.path.abspath(os.path.dirname(__file__) + '/../config/')
WRAPPERDIR = os.path.abspath(os.path.dirname(__file__) + '/../wrappers/')

#clam.common.formats is deliberately imported _at the end_

DISALLOWINSHELLSAFE = ('|','&',';','!','<','>','{','}','`','\n','\r','\t')

CUSTOM_FORMATS = []  #will be injected
CUSTOM_VIEWERS = []  #will be injected

class BadRequest(Exception):
    def __init__(self):
        super(BadRequest, self).__init__()
    def __str__(self):
        return "Bad Request"

class NotFound(Exception):
    """Raised on 404 - Not Found Errors"""
    def __init__(self, msg=""):
        self.msg = msg
        super(NotFound, self).__init__()
    def __str__(self):
        return "Not Found: " +  self.msg

class PermissionDenied(Exception):
    """Raised on 403 - Permission Denied Errors (but only if no CLAM XML response is provided)"""
    def __init__(self, msg = ""):
        self.msg = msg
        super(PermissionDenied, self).__init__()
    def __str__(self):
        if isinstance(clam.common.data,CLAMData):
            return "Permission Denied"
        else:
            return "Permission Denied: " + self.msg

class ServerError(Exception):
    """Raised on 500 - Internal Server Error. Indicates that something went wrong on the server side."""
    def __init__(self, msg = ""):
        self.msg = msg
        super(ServerError, self).__init__()
    def __str__(self):
        return "Server Error: " + self.msg

class AuthRequired(Exception):
    """Raised on 401 - Authentication Required error. Service requires authentication, pass user credentials in CLAMClient constructor."""
    def __init__(self, msg = ""):
        self.msg = msg
        super(AuthRequired, self).__init__()
    def __str__(self):
        return "Authorization Required: " + self.msg

class NoConnection(Exception):
    def __init__(self):
        super(NoConnection, self).__init__()
    def __str__(self):
        return "Can't establish a connection with the server"


class UploadError(Exception):
    def __init__(self, msg = ""):
        self.msg = msg
        super(UploadError, self).__init__()
    def __str__(self):
        return "Error during Upload: " + self.msg

class ParameterError(Exception):
    """Raised on Parameter Errors, i.e. when a parameter does not validate, is missing, or is otherwise set incorrectly."""
    def __init__(self, msg = ""):
        self.msg = msg
        super(ParameterError, self).__init__()
    def __str__(self):
        return "Error setting parameter: " + self.msg

class TimeOut(Exception):
    def __init__(self):
        super(TimeOut, self).__init__()
    def __str__(self):
        return "Connection with server timed-out"

if sys.version < '3':
    #Python 2 used IOError instead, create a subclass
    class FileNotFoundError(IOError): #pylint: disable=redefined-builtin
        pass

def processhttpcode(code, allowcodes=None):
    if allowcodes is None: allowcodes = ()
    if not isinstance(code, int): code = int(code)
    if (code >= 200 and code <= 299) or code in allowcodes:
        return code
    elif code == 400:
        raise BadRequest()
    elif code == 401:
        raise AuthRequired()
    elif code == 403:
        raise PermissionDenied()
    elif code == 404:
        raise NotFound()
    elif code == 500:
        raise ServerError()
    else:
        raise UploadError()


def parsexmlstring(node):
    if sys.version < '3' and isinstance(node,unicode): #pylint: disable=undefined-variable
        return ElementTree.parse(StringIO(node.encode('utf-8'))).getroot()
    elif sys.version >= '3' and isinstance(node,str):
        return ElementTree.parse(BytesIO(node.encode('utf-8'))).getroot()
    elif sys.version < '2' and isinstance(node,str):
        return ElementTree.parse(StringIO(node)).getroot()
    elif sys.version >= '3' and isinstance(node,bytes):
        return ElementTree.parse(BytesIO(node)).getroot()
    else:
        raise Exception("Expected XML string, don't know how to parse type " + str(type(node)))




class FormatError(Exception):
    """This Exception is raised when the CLAM response is not in the valid CLAM XML format"""
    def __init__(self, value):
        self.value = value
        super(FormatError,self).__init__()
    def __str__(self):
        return "Not a valid CLAM XML response"

class HTTPError(Exception):
    """This Exception is raised when certain data (such a metadata), can't be retrieved over HTTP"""
    pass

class AuthenticationRequired(Exception):
    """This Exception is raised when authentication is required but has not been provided"""
    pass

class ConfigurationError(Exception):
    """This Exception is raised when authentication is required but has not been provided"""
    pass

class CLAMFile:
    basedir = ''

    def __init__(self, projectpath, filename, loadmetadata = True, client = None, requiremetadata=False):
        """Create a CLAMFile object, providing immediate transparent access to CLAM Input and Output files, remote as well as local! And including metadata."""
        self.remote = (projectpath[0:7] == 'http://' or projectpath[0:8] == 'https://')
        self.projectpath = projectpath
        self.filename = filename
        self.metadata = None
        self.client = client
        if loadmetadata:
            try:
                self.loadmetadata()
            except IOError:
                if requiremetadata:
                    raise
            except HTTPError:
                if requiremetadata:
                    raise

        self.viewers = []
        self.converters = []


    def attachviewers(self, profiles):
        """Attach viewers *and converters* to file, automatically scan all profiles for outputtemplate or inputtemplate"""
        if self.metadata:
            template = None
            for profile in profiles:
                if isinstance(self, CLAMInputFile):
                    for t in profile.input:
                        if self.metadata.inputtemplate == t.id:
                            template = t
                            break
                elif isinstance(self, CLAMOutputFile) and self.metadata and self.metadata.provenance:
                    for t in profile.outputtemplates():
                        if self.metadata.provenance.outputtemplate_id == t.id:
                            template = t
                            break
                else:
                    raise NotImplementedError #Is ok, nothing to implement for now
                if template:
                    break
            if template and template.viewers:
                for viewer in template.viewers:
                    self.viewers.append(viewer)
            if template and template.converters:
                for converter in template.converters:
                    self.converters.append(converter)

    def metafilename(self):
        """Returns the filename for the metadata file (not full path). Only used for local files."""
        metafilename = os.path.dirname(self.filename)
        if metafilename: metafilename += '/'
        metafilename += '.' + os.path.basename(self.filename) + '.METADATA'
        return metafilename

    def loadmetadata(self):
        """Load metadata for this file. This is usually called automatically upon instantiation, except if explicitly disabled. Works both locally as well as for clients connecting to a CLAM service."""
        if not self.remote:
            metafile = self.projectpath + self.basedir + '/' + self.metafilename()
            if os.path.exists(metafile):
                f = io.open(metafile, 'r',encoding='utf-8')
                xml = "".join(f.readlines())
                f.close()
            else:
                raise IOError(2, "No metadata found, expected " + metafile )
        else:
            if self.client:
                requestparams = self.client.initrequest()
            else:
                requestparams = {}
            response = requests.get(self.projectpath + self.basedir + '/' + self.filename + '/metadata', **requestparams)
            if response.status_code != 200:
                extramsg = ""
                if not self.client: extramsg = "No client was associated with this CLAMFile, associating a client is necessary when authentication is needed"
                raise HTTPError(2, "Can't download metadata for " + self.filename + ". " + extramsg)
            xml = response.text


        #parse metadata
        try:
            self.metadata = CLAMMetaData.fromxml(xml, self) #returns CLAMMetaData object (or child thereof)
        except ElementTree.XMLSyntaxError:
            raise ValueError("Metadata is not XML! Contents: " + xml)

    def __iter__(self):
        """Read the lines of the file, one by one without loading the file into memory."""
        if not self.remote:
            fullpath = self.projectpath + self.basedir + '/' + self.filename
            if not os.path.exists(fullpath):
                raise FileNotFoundError("No such file or directory: " + fullpath )
            if self.metadata and 'encoding' in self.metadata:
                for line in io.open(fullpath, 'r', encoding=self.metadata['encoding']).readlines():
                    yield line
            else:
                for line in io.open(fullpath, 'rb').readlines():
                    yield line
        else:
            fullpath = self.projectpath + self.basedir + '/' + self.filename
            if self.client:
                requestparams = self.client.initrequest()
            else:
                requestparams = {}
            requestparams['stream'] = True
            response = requests.get(self.projectpath + self.basedir + '/' + self.filename, **requestparams)
            if self.metadata and 'encoding' in self.metadata:
                for line in response.iter_lines():
                    #\n is stripped, re-add (should also work fine on binary files)
                    if sys.version[0] < '3' and not isinstance(line,unicode): #pylint: disable=undefined-variable
                        yield unicode(line, self.metadata['encoding']) + "\n" #pylint: disable=undefined-variable
                    elif sys.version[0] >= '3' and not isinstance(line,str):
                        yield str(line, self.metadata['encoding']) + "\n"
                    else:
                        yield line + b'\n'
            else:
                CHUNKSIZE = 64*1024
                for line in response.iter_content(CHUNKSIZE):
                    yield line

    def delete(self):
        """Delete this file"""
        if not self.remote:
            if not os.path.exists(self.projectpath + self.basedir + '/' + self.filename):
                return False
            else:
                os.unlink(self.projectpath + self.basedir + '/' + self.filename)

            #Remove metadata
            metafile = self.projectpath + self.basedir + '/' + self.metafilename()
            if os.path.exists(metafile):
                os.unlink(metafile)

            #also remove any .*.INPUTTEMPLATE.* links that pointed to this file: simply remove all dead links
            for linkf,realf in clam.common.util.globsymlinks(self.projectpath + self.basedir + '/.*.INPUTTEMPLATE.*'):
                if not os.path.exists(realf):
                    os.unlink(linkf)

            return True
        else:
            if self.client:
                requestparams = self.client.initrequest()
            else:
                requestparams = {}
            requests.delete( self.projectpath + self.basedir + '/' + self.filename, **requestparams)
            return True


    def readlines(self):
        """Loads all lines in memory"""
        return list(iter(self))

    def read(self):
        """Loads all lines in memory"""
        lines = self.readlines()
        if self.metadata and 'encoding' in self.metadata:
            encoding = self.metadata['encoding']
        else:
            encoding = 'utf-8'
        if sys.version < '3':
            return "\n".join( unicode(line, 'utf-8') if isinstance(line, str) else line for line in lines)
        else:
            return "\n".join( str(line, 'utf-8') if isinstance(line, bytes) else line for line in lines)


    def copy(self, target, timeout=500):
        """Copy or download this file to a new local file"""

        if self.metadata and 'encoding' in self.metadata:
            with io.open(target,'w', encoding=self.metadata['encoding']) as f:
                for line in self:
                    f.write(line)
        else:
            with io.open(target,'wb') as f:
                for line in self:
                    if sys.version < '3' and isinstance(line,unicode): #pylint: disable=undefined-variable
                        f.write(line.encode('utf-8'))
                    elif sys.version >= '3' and isinstance(line,str):
                        f.write(line.encode('utf-8'))
                    else:
                        f.write(line)

    def validate(self):
        """Validate this file. Returns a boolean."""
        if self.metadata:
            return self.metadata.validate()
        else:
            return False


    def __str__(self):
        return self.projectpath + self.basedir + '/' + self.filename

class CLAMInputFile(CLAMFile):
    basedir = "input"

class CLAMOutputFile(CLAMFile):
    basedir = "output"

def getclamdata(filename, custom_formats=None, custom_viewers=None):
    global CUSTOM_FORMATS, CUSTOM_VIEWERS  #pylint: disable=global-statement
    """This function reads the CLAM Data from an XML file. Use this to read
    the clam.xml file from your system wrapper. It returns a CLAMData instance.

    If you make use of CUSTOM_FORMATS, you need to pass the CUSTOM_FORMATS list as 2nd argument.
    """
    f = io.open(filename,'r',encoding='utf-8')
    xml = f.read(os.path.getsize(filename))
    f.close()
    if custom_formats:
        CUSTOM_FORMATS = custom_formats #dependency injection for CUSTOM_FORMATS
    if custom_viewers:
        CUSTOM_VIEWERS = custom_viewers
    return CLAMData(xml, None, True)


def processparameter(postdata, parameter, user=None):
    errors = False
    commandlineparam = ""

    if parameter.access(user):
        try:
            postvalue = parameter.valuefrompostdata(postdata)
        except Exception: #pylint: disable=broad-except
            clam.common.util.printlog("Invalid value, unable to interpret parameter " + parameter.id + ", ...")
            parameter.error = "Invalid value, unable to interpret"
            return True, parameter, ''

        if postvalue is not None:
            clam.common.util.printdebug("Setting parameter '" + parameter.id + "' to: " + repr(postvalue) + ' (from postdata)')
            if parameter.set(postvalue): #may generate an error in parameter.error
                p = parameter.compilearg() #shell-safe
                if p:
                    commandlineparam = p
            else:
                if not parameter.error: parameter.error = "Something undefined went wrong whilst setting this parameter!" #shouldn't happen
                clam.common.util.printlog("Unable to set " + parameter.id + ": " + parameter.error)
                errors = True
        elif parameter.required:
            #Not all required parameters were filled!
            parameter.error = "This parameter is mandatory and must be set!"
            errors = True

    return errors, parameter, commandlineparam

def processparameters(postdata, parameters, user=None):
    #we're going to modify parameter values, this we can't do
    #on the global variable, that won't be thread-safe, we first
    #make a (shallow) copy and act on that

    commandlineparams = [] #for $PARAMETERS
    errors = False

    newparameters = [] #in same style as input (i.e. with or without groups)
    tempparlist = [] #always a list of parameters

    if all([isinstance(x,tuple) for x in parameters ]):
        for parametergroup, parameterlist in parameters:
            newparameterlist = []
            for parameter in parameterlist:
                error, parameter, commandlineparam = processparameter(postdata, copy(parameter), user)
                errors = errors or error
                newparameterlist.append(parameter)
                tempparlist.append(parameter)
                if commandlineparam:
                    commandlineparams.append(commandlineparam)
            newparameters.append( (parametergroup, newparameterlist) )
    elif all([isinstance(x,clam.common.parameters.AbstractParameter) for x in parameters]):
        for parameter in parameters:
            error, parameter, commandlineparam = processparameter(postdata, copy(parameter), user)
            errors = errors or error
            newparameters.append(copy(parameter))
            if commandlineparam:
                commandlineparams.append(commandlineparam)
        tempparlist = newparameters
    else:
        raise Exception("Invalid parameters")

    #solve dependency issues now all values have been set:
    for parameter in tempparlist:
        if parameter.constrainable() and (parameter.forbid or parameter.require):
            for parameter2 in tempparlist:
                if parameter.forbid and parameter2.id in parameter.forbid and parameter2.constrainable():
                    parameter.error = parameter2.error = "Setting parameter '" + parameter.name + "' together with '" + parameter2.name + "'  is forbidden"
                    clam.common.util.printlog("Setting " + parameter.id + " and " + parameter2.id + "' together is forbidden")
                    errors = True
                if parameter.require and parameter2.id in parameter.require and not parameter2.constrainable():
                    parameter.error = parameter2.error = "Parameter '" + parameter.name + "' has to be set with '" + parameter2.name + "'  is"
                    clam.common.util.printlog("Setting " + parameter.id + " requires you also set " + parameter2.id )
                    errors = True

    return errors, newparameters, commandlineparams

class CLAMData(object):
    """Instances of this class hold all the CLAM Data that is automatically extracted from CLAM
    XML responses. Its member variables are:

        * ``baseurl``         - The base URL to the service (string)
        * ``projecturl``      - The full URL to the selected project, if any  (string)
        * ``status``          - Can be: ``clam.common.status.READY`` (0),``clam.common.status.RUNNING`` (1), or ``clam.common.status.DONE`` (2)
        * ``statusmessage``   - The latest status message (string)
        * ``completion``      - An integer between 0 and 100 indicating
                          the percentage towards completion.
        * ``parameters``      - List of parameters (but use the methods instead)
        * ``profiles``        - List of profiles (``[ Profile ]``)
        * ``program``         - A Program instance (or None). Describes the expected outputfiles given the uploaded inputfiles. This is the concretisation of the matching profiles.
        * ``input``           - List of input files  (``[ CLAMInputFile ]``); use ``inputfiles()`` instead for easier access
        * ``output``          - List of output files (``[ CLAMOutputFile ]``)
        * ``projects``        - List of project IDs (``[ string ]``)
        * ``corpora``         - List of pre-installed corpora
        * ``errors``          - Boolean indicating whether there are errors in parameter specification
        * ``errormsg``        - String containing an error message
        * ``oauth_access_token``  -  OAuth2 access token (empty if not used, string)

    Note that depending on the current status of the project, not all may be available.
    """

    def __init__(self, xml, client=None, localroot = False, projectpath=None, loadmetadata=True):
        """Initialises a CLAMData object by passing pass a string containing the full CLAM XML response. It will be automatically parsed. This is usually not called directly but instantiated in system wrapper scripts using::

            data = clam.common.data.getclamdata("clam.xml")

        Or ``CLAMCLient`` is used, most responses are ``CLAMData`` instances.
        """
        self.xml = xml

        self.system_id = ""
        self.system_name = ""
        self.system_version = ""
        self.system_email = ""
        self.description = ""

        #: String containing the base URL of the webserivice
        self.baseurl = ''

        #: String containing the full URL to the project, if a project was indeed selected
        self.projecturl = ''

        #: The current status of the service, returns clam.common.status.READY (1), clam.common.status.RUNNING (2), or clam.common.status.DONE (3)
        self.status = clam.common.status.READY

        #: The current status of the service in a human readable message
        self.statusmessage = ""
        self.completion = 0

        #: This contains a list of (parametergroup, [parameters]) tuples.
        self.parameters = []

        #: List of profiles ([ Profile ])
        self.profiles = []

        #: Program instance. Describes the expected outputfiles given the uploaded inputfiles. This is the concretisation of the matching profiles.
        self.program = None

        #:  List of pre-installed corpora
        self.corpora = []

        #: List of input files ([ CLAMInputFile ])
        self.input = []

        #: List of output files ([ CLAMOutputFile ])
        self.output = []

        #: Automatically load metadata for input and output files? (default: True)
        self.loadmetadata = loadmetadata

        #: List of projects ([ string ])
        self.projects = None

        #: Boolean indicating whether there are errors in parameter specification
        self.errors = False

        #: String containing an error message if an error occured
        self.errormsg = ""

        self.client = client


        self.parseresponse(xml, localroot)



    def parseresponse(self, xml, localroot = False):
        """Parses CLAM XML, there's usually no need to call this directly"""
        root = parsexmlstring(xml)
        if root.tag != 'clam':
            raise FormatError("CLAM root tag not found")

        self.system_id = root.attrib['id']
        self.system_name = root.attrib['name']
        if 'project' in root.attrib:
            self.project = root.attrib['project']
        else:
            self.project = None
        if 'baseurl' in root.attrib:
            self.baseurl = root.attrib['baseurl']
            if self.project:
                if localroot is True: #implicit, assume CWD
                    self.remote = False
                    self.projecturl = '' #relative directory (assume CWD is project directory, as is the case when wrapper scripts are called)
                elif localroot: #explicit
                    self.remote = False
                    self.projecturl = localroot + '/' + self.project + '/' #explicit directory
                else:
                    self.remote = True #no directory: remote URL
                    self.projecturl = self.baseurl + '/' + self.project + '/'

        if 'user' in root.attrib:
            self.user = root.attrib['user']
        else:
            self.user = None

        self.oauth_access_token = ""
        if 'oauth_access_token' in root.attrib:
            self.oauth_access_token = root.attrib['oauth_access_token']

        for node in root: #pylint: disable=too-many-nested-blocks
            if node.tag == "description":
                self.description = node.text
            elif node.tag == "version":
                self.system_version = node.text
            elif node.tag == "email":
                self.system_email = node.text
            elif node.tag == 'status':
                self.status = int(node.attrib['code'])
                self.statusmessage  = node.attrib['message']
                self.completion  = node.attrib['completion']
                if 'errors' in node.attrib:
                    self.errors = ((node.attrib['errors'] == 'yes') or (node.attrib['errors'] == '1'))
                if 'errormsg' in node.attrib:
                    self.errormsg = node.attrib['errormsg']
            elif node.tag == 'parameters':
                for parametergroupnode in node:
                    if parametergroupnode.tag == 'parametergroup':
                        parameterlist = []
                        for parameternode in parametergroupnode:
                            if parameternode.tag in vars(clam.common.parameters):
                                parameterlist.append(vars(clam.common.parameters)[parameternode.tag].fromxml(parameternode))
                            else:
                                raise Exception("Expected parameter class '" + parameternode.tag + "', but not defined!")
                        self.parameters.append( (parametergroupnode.attrib['name'], parameterlist) )
            elif node.tag == 'corpora':
                for corpusnode in node:
                    if corpusnode.tag == 'corpus':
                        self.corpora.append(corpusnode.value)
            elif node.tag == 'profiles':
                for subnode in node:
                    if subnode.tag == 'profile':
                        self.profiles.append(Profile.fromxml(subnode))
            elif node.tag == 'input':
                for filenode in node:
                    if filenode.tag == 'file':
                        for n in filenode:
                            if n.tag == 'name':
                                self.input.append( CLAMInputFile( self.projecturl, n.text, self.loadmetadata, self.client,True) )
            elif node.tag == 'output':
                for filenode in node:
                    if filenode.tag == 'file':
                        for n in filenode:
                            if n.tag == 'name':
                                self.output.append( CLAMOutputFile( self.projecturl, n.text, self.loadmetadata, self.client ) )
            elif node.tag == 'projects':
                self.projects = []
                for projectnode in node:
                    if projectnode.tag == 'project':
                        self.projects.append(projectnode.text)
            elif node.tag == 'program':
                self.program = Program(self.projecturl, [ int(i) for i in node.attrib['matchedprofiles'].split(',') ] )
                for outputfilenode in node:
                    if outputfilenode.tag == 'outputfile':
                        inputfound = False
                        for inputfilenode in outputfilenode:
                            if inputfilenode.tag == 'inputfile':
                                inputfound = True
                                self.program.add(outputfilenode.attrib['name'],outputfilenode.attrib['template'],inputfilenode.attrib['name'], inputfilenode.attrib['template'])
                        if not inputfound:
                            self.program.add(outputfilenode.attrib['name'],outputfilenode.attrib['template'])

    def outputtemplate(self, template_id):
        """Get an output template by ID"""
        for profile in self.profiles:
            for outputtemplate in profile.outputtemplates():
                if outputtemplate.id == template_id:
                    return outputtemplate
        return KeyError("Outputtemplate " + template_id + " not found")


    def commandlineargs(self):
        """Obtain a string of all parameters, using the paramater flags they were defined with, in order to pass to an external command. This is shell-safe by definition."""
        commandlineargs = []
        for parametergroup, parameters in self.parameters: #pylint: disable=unused-variable
            for parameter in parameters:
                p = parameter.compilearg()
                if p:
                    commandlineargs.append(p)
        return " ".join(commandlineargs)


    def parameter(self, parameter_id):
        """Return the specified global parameter (the entire object, not just the value)"""
        for parametergroup, parameters in self.parameters: #pylint: disable=unused-variable
            for parameter in parameters:
                if parameter.id == parameter_id:
                    return parameter
        raise KeyError("No such parameter exists: " + parameter_id )

    def __getitem__(self, parameter_id):
        """Return the value of the specified global parameter"""
        try:
            return self.parameter(parameter_id).value
        except KeyError:
            raise

    def get(self, parameter_id, default=None):
        try:
            return self[parameter_id]
        except KeyError:
            return default

    def __setitem__(self, parameter_id, value):
        """Set the value of the specified global parameter"""
        for parametergroup, parameters in self.parameters: #pylint: disable=unused-variable
            for parameter in parameters:
                if parameter.id == parameter_id:
                    parameter.set(value)
                    return True
        raise KeyError

    def __contains__(self, parameter_id):
        """Check if a global parameter with the specified ID exists. Returns a boolean."""
        for parametergroup, parameters in self.parameters: #pylint: disable=unused-variable
            for parameter in parameters:
                if parameter.id == parameter_id:
                    return True
        return False

    def parametererror(self):
        """Return the first parameter error, or False if there is none"""
        for parametergroup, parameters in self.parameters: #pylint: disable=unused-variable
            for parameter in parameters:
                if parameter.error:
                    return parameter.error
        return False

    def passparameters(self):
        """Return all parameters as {id: value} dictionary"""
        paramdict = {}
        for parametergroup, params in self.parameters: #pylint: disable=unused-variable
            for parameter in params:
                if parameter.value:
                    if isinstance(parameter.value, list):
                        paramdict[parameter.id] = ",".join(parameter.value)
                    else:
                        paramdict[parameter.id] = parameter.value
        return paramdict


    def inputtemplates(self):
        """Return all input templates as a list (of InputTemplate instances)"""
        l = []
        for profile in self.profiles:
            l += profile.input
        return l

    def inputtemplate(self,template_id):
        """Return the inputtemplate with the specified ID. This is used to resolve a inputtemplate ID to an InputTemplate object instance"""
        for profile in self.profiles:
            for inputtemplate in profile.input:
                if inputtemplate.id == template_id:
                    return inputtemplate
        raise Exception("No such input template: " + repr(template_id))

    def inputfile(self, inputtemplate=None):
        """Return the inputfile for the specified inputtemplate, if ``inputtemplate=None``, inputfile is returned regardless of inputtemplate. This function may only return 1 and returns an error when multiple input files can be returned, use ``inputfiles()`` instead."""
        inputfiles = list(self.inputfiles(inputtemplate))
        if len(inputfiles) < 1:
            raise Exception("No such input file")
        elif len(inputfiles) > 1:
            raise Exception("Multiple input files matched. Use inputfiles() instead!")
        return inputfiles[0]

    def matchingprofiles(self):
        """Generator yielding all matching profiles"""
        for i in self.matchedprofiles:
            yield self.profiles[i]

    def inputfiles(self, inputtemplate=None):
        """Generator yielding all inputfiles for the specified inputtemplate, if ``inputtemplate=None``, inputfiles are returned regardless of inputtemplate."""
        if isinstance(inputtemplate, InputTemplate):
            #ID suffices:
            inputtemplate = inputtemplate.id
        for inputfile in self.input:
            if not inputtemplate or inputfile.metadata.inputtemplate == inputtemplate:
                yield inputfile

def sanitizeparameters(parameters):
    """Construct a dictionary of parameters, for internal use only"""
    if not isinstance(parameters,dict):
        d = {}
        for x in parameters:
            if isinstance(x,tuple) and len(x) == 2:
                for parameter in x[1]:
                    d[parameter.id] = parameter
            elif isinstance(x, clam.common.parameters.AbstractParameter):
                d[x.id] = x
        return d
    else:
        return parameters



def profiler(profiles, projectpath,parameters,serviceid,servicename,serviceurl,printdebug=None):
    """Given input files and parameters, produce metadata for outputfiles. Returns a list of matched profiles (empty if none match), and a program."""

    parameters = sanitizeparameters(parameters)

    matched = []
    program = Program(projectpath)
    for profile in profiles:
        if profile.match(projectpath, parameters)[0]:
            matched.append(profile)
            program.update( profile.generate(projectpath,parameters,serviceid,servicename,serviceurl) )

    return matched, program






class Profile(object):
    def __init__(self, *args):
        """Create a Profile. Arguments can be of class InputTemplate, OutputTemplate or ParameterCondition"""

        self.input = []
        self.output = []

        for arg in args:
            if isinstance(arg, InputTemplate):
                self.input.append(arg)
            elif isinstance(arg, OutputTemplate):
                self.output.append(arg)
            elif isinstance(arg, ParameterCondition):
                self.output.append(arg)
            elif arg is None:
                pass

        #Check for orphan OutputTemplates. OutputTemplates must have a parent (only outputtemplates with filename, unique=True may be parentless)
        for o in self.output:
            if isinstance(o, ParameterCondition):
                for o in o.allpossibilities():
                    if not o:
                        continue
                    if not isinstance(o, OutputTemplate):
                        raise Exception("ParameterConditions in profiles must always evaluate to OutputTemplate, not " + o.__class__.__name__ + "!")
                    parent = o.findparent(self.input)
                    if parent:
                        o.parent = parent
                        if not o.parent and (not (o.filename and o.unique)):
                            raise Exception("Outputtemplate '" + o.id + "' has no parent defined, and none could be found automatically!")
            elif not o.parent:
                o.parent = o.findparent(self.input)
                if not o.parent and (not (o.filename and o.unique)):
                    raise Exception("Outputtemplate '" + o.id + "' has no parent defined, and none could be found automatically!")

        #Sanity check (note: does not consider ParameterConditions!)
        for o in self.output: #pylint: disable=too-many-nested-blocks
            for o2 in self.output:
                if not isinstance(o, ParameterCondition) and not isinstance(o2, ParameterCondition) and o.id != o2.id:
                    if o.filename == o2.filename:
                        if not o.filename:
                            #no filename specified (which means it's inherited from parent as is)
                            if o.extension == o2.extension: #extension is the same (or both none)
                                if o.parent == o2.parent:
                                    raise Exception("Output templates '" + o.id + "' and '" + o2.id + "' describe identically named output files, this is not possible. They define no filename and no extension (or equal extension) so both inherit the same filename from the same parent. Use filename= or extension= to distinguish the two.")
                        else:
                            raise Exception("Output templates '" + o.id + "' and '" + o2.id + "' describe identically named output files, this is not possible. Use filename= or extension= to distinguish the two.")




    def match(self, projectpath, parameters):
        """Check if the profile matches all inputdata *and* produces output given the set parameters. Returns a boolean"""
        parameters = sanitizeparameters(parameters)

        mandatory_absent = [] #list of input templates that are missing but mandatory
        optional_absent = [] #list of absent but optional input templates

        #check if profile matches inputdata (if there are no inputtemplate, this always matches intentionally!)
        for inputtemplate in self.input:
            if not inputtemplate.matchingfiles(projectpath):
                if inputtemplate.optional:
                    optional_absent.append(inputtemplate)
                else:
                    mandatory_absent.append(inputtemplate)

        if mandatory_absent:
            return False, mandatory_absent

        #check if output is produced
        if not self.output: return False, mandatory_absent
        for outputtemplate in self.output:
            if isinstance(outputtemplate, ParameterCondition):
                outputtemplate = outputtemplate.evaluate(parameters)
            if not outputtemplate:
                continue
            assert isinstance(outputtemplate, OutputTemplate)
            if outputtemplate.parent:
                if outputtemplate.getparent(self) not in optional_absent: #pylint: disable=protected-access
                    return True, optional_absent
            else:
                return True, optional_absent

        return False, optional_absent

    def matchingfiles(self, projectpath):
        """Return a list of all inputfiles matching the profile (filenames)"""
        l = []
        for inputtemplate in self.input:
            l += inputtemplate.matchingfiles(projectpath)
        return l

    def outputtemplates(self):
        """Returns all outputtemplates, resolving ParameterConditions to all possibilities"""
        outputtemplates = []
        for o in self.output:
            if isinstance(o, ParameterCondition):
                outputtemplates += o.allpossibilities()
            else:
                assert isinstance(o, OutputTemplate)
                outputtemplates.append(o)
        return outputtemplates


    def generate(self, projectpath, parameters, serviceid, servicename,serviceurl):
        """Generate output metadata on the basis of input files and parameters. Projectpath must be absolute. Returns a Program instance.  """

        #Make dictionary of parameters
        parameters = sanitizeparameters(parameters)

        program = Program(projectpath, [self])

        match, optional_absent = self.match(projectpath, parameters) #Does the profile match?
        if match: #pylint: disable=too-many-nested-blocks

            #gather all input files that match
            inputfiles = self.matchingfiles(projectpath) #list of (seqnr, filename,inputtemplate) tuples

            inputfiles_full = [] #We need the full CLAMInputFiles for generating provenance data
            for seqnr, filename, inputtemplate in inputfiles: #pylint: disable=unused-variable
                inputfiles_full.append(CLAMInputFile(projectpath, filename))

            for outputtemplate in self.output:
                if isinstance(outputtemplate, ParameterCondition):
                    outputtemplate = outputtemplate.evaluate(parameters)

                #generate output files
                if outputtemplate:
                    if isinstance(outputtemplate, OutputTemplate):
                        #generate provenance data
                        provenancedata = CLAMProvenanceData(serviceid,servicename,serviceurl,outputtemplate.id, outputtemplate.label,  inputfiles_full, parameters)

                        create = True
                        if outputtemplate.parent:
                            if outputtemplate.getparent(self) in optional_absent:
                                create = False

                        if create:
                            for inputtemplate, inputfilename, outputfilename, metadata in outputtemplate.generate(self, parameters, projectpath, inputfiles, provenancedata):
                                clam.common.util.printdebug("Writing metadata for outputfile " + outputfilename)
                                metafilename = os.path.dirname(outputfilename)
                                if metafilename: metafilename += '/'
                                metafilename += '.' + os.path.basename(outputfilename) + '.METADATA'
                                f = io.open(projectpath + '/output/' + metafilename,'w',encoding='utf-8')
                                f.write(metadata.xml())
                                f.close()
                                program.add(outputfilename, outputtemplate, inputfilename, inputtemplate)
                    else:
                        raise TypeError("OutputTemplate expected, but got " + outputtemplate.__class__.__name__)

        return program


    def xml(self, indent = ""):
        """Produce XML output for the profile"""
        xml = "\n" + indent + "<profile>\n"
        xml += indent + " <input>\n"
        for inputtemplate in self.input:
            xml += inputtemplate.xml(indent +"    ") + "\n"
        xml += indent + " </input>\n"
        xml += indent + " <output>\n"
        for outputtemplate in self.output:
            xml += outputtemplate.xml(indent +"    ") + "\n" #works for ParameterCondition as well!
        xml += indent + " </output>\n"
        xml += indent + "</profile>\n"
        return xml

    def out(self, indent = ""):
        o = indent + "Profile"
        o += indent + "\tInput"
        for inputtemplate in self.input:
            o += inputtemplate.out(indent +"    ") + "\n"
        o += indent + "\tOutput"
        for outputtemplate in self.output:
            o += outputtemplate.out(indent +"    ") + "\n"

        return o

    @staticmethod
    def fromxml(node):
        """Return a profile instance from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element): #pylint: disable=protected-access
            node = parsexmlstring(node)

        args = []

        if node.tag == 'profile':
            for node in node:
                if node.tag == 'input':
                    for subnode in node:
                        if subnode.tag.lower() == 'inputtemplate':
                            args.append(InputTemplate.fromxml(subnode))
                elif node.tag == 'output':
                    for subnode in node:
                        if subnode.tag.lower() == 'outputtemplate':
                            args.append(OutputTemplate.fromxml(subnode))
                        elif subnode.tag.lower() == 'parametercondition':
                            args.append(ParameterCondition.fromxml(subnode))
        return Profile(*args)

class Program(dict):
    """A Program is the concretisation of Profile. It describes the exact output files that will be created on the basis of what input files. This is in essence a dictionary
    structured as follows: ``{outputfilename: (outputtemplate, inputfiles)}`` in which ``inputfiles`` is a dictionary ``{inputfilename: inputtemplate}``"""

    def __init__(self, projectpath, matchedprofiles=None):
        self.projectpath=projectpath
        if matchedprofiles is None:
            self.matchedprofiles=[]
        else:
            self.matchedprofiles=matchedprofiles
        super(Program,self).__init__()

    def update(self, src):
        self.projectpath = src.projectpath
        self.matchedprofiles=list(set(self.matchedprofiles+ src.matchedprofiles))
        super(Program,self).update(src)

    def add(self, outputfilename, outputtemplate, inputfilename=None, inputtemplate=None):
        """Add a new path to the program"""
        if isinstance(outputtemplate,OutputTemplate):
            outputtemplate = outputtemplate.id
        if isinstance(inputtemplate,InputTemplate):
            inputtemplate = inputtemplate.id
        if outputfilename in self:
            outputtemplate, inputfiles = self[outputfilename]
            if inputfilename and inputtemplate:
                inputfiles[inputfilename] = inputtemplate
        else:
            if inputfilename and inputtemplate:
                self[outputfilename] = (outputtemplate, {inputfilename: inputtemplate})
            else:
                self[outputfilename] = (outputtemplate, {})

    def outputpairs(self):
        """Iterates over all (outputfilename, outputtemplate) pairs"""
        for outputfilename, (outputtemplate, inputfiles) in self.items():
            yield outputfilename, outputtemplate

    def inputpairs(self, outputfilename):
        """Iterates over all (inputfilename, inputtemplate) pairs for a specific output filename"""
        for inputfilename, inputtemplate in self[outputfilename][1]:
            yield inputfilename, inputtemplate

    def getoutputfiles(self, loadmetadata=True, client=None,requiremetadata=False):
        """Iterates over all output files and their output template. Yields (CLAMOutputFile, str:outputtemplate_id) tuples. The last three arguments are passed to its constructor."""
        for outputfilename, outputtemplate in self.outputpairs():
            yield CLAMOutputFile(self.projectpath, outputfilename, loadmetadata,client,requiremetadata), outputtemplate

    def getinputfiles(self, outputfile, loadmetadata=True, client=None,requiremetadata=False):
        """Iterates over all input files for the specified outputfile (you may pass a CLAMOutputFile instance or a filename string). Yields (CLAMInputFile,str:inputtemplate_id) tuples. The last three arguments are passed to its constructor."""
        if isinstance(outputfile, CLAMOutputFile):
            outputfilename = str(outputfile).replace(os.path.join(self.projectpath,'output/'),'')
        else:
            outputfilename = outputfile
        outputtemplate, inputfiles = self[outputfilename]
        for inputfilename, inputtemplate in inputfiles.items():
            yield CLAMInputFile(self.projectpath, inputfilename, loadmetadata,client,requiremetadata), inputtemplate

    def getinputfile(self, outputfile, loadmetadata=True, client=None,requiremetadata=False):
        """Grabs one input file for the specified output filename (raises a KeyError exception if there is no such output, StopIteration if there are no input files for it). Shortcut for getinputfiles()"""
        if isinstance(outputfile, CLAMOutputFile):
            outputfilename = str(outputfile).replace(os.path.join(self.projectpath,'output/'),'')
        else:
            outputfilename = outputfile
        if outputfilename not in self:
            raise KeyError("No such outputfile " + outputfilename)
        try:
            return next(self.getinputfiles(outputfile,loadmetadata,client,requiremetadata))
        except StopIteration:
            raise StopIteration("No input files for outputfile " + outputfilename)

    def getoutputfile(self, loadmetadata=True, client=None,requiremetadata=False):
        """Grabs one output file (raises a StopIteration exception if there is none). Shortcut for getoutputfiles()"""
        return next(self.getoutputfiles(loadmetadata,client,requiremetadata))

class RawXMLProvenanceData(object):
    def __init__(self, data):
        self.data = data

    def xml(self):
        if isinstance(self.data, ElementTree._Element): #pylint: disable=protected-access
            return ElementTree.tostring(self.data, pretty_print = True)
        else:
            return self.data

class CLAMProvenanceData(object):
    """Holds provenance data"""

    def __init__(self, serviceid, servicename, serviceurl, outputtemplate_id, outputtemplate_label, inputfiles, parameters = None, timestamp = None):
        self.serviceid = serviceid
        self.servicename = servicename
        self.serviceurl = serviceurl
        self.outputtemplate_id = outputtemplate_id
        self.outputtemplate_label = outputtemplate_label
        if parameters:
            if isinstance(parameters, dict):
                assert all([isinstance(x,clam.common.parameters.AbstractParameter) for x in parameters.values()])
                self.parameters = parameters
            else:
                assert all([isinstance(x,clam.common.parameters.AbstractParameter) for x in parameters])
                self.parameters = parameters
        else:
            self.parameters = []

        if timestamp:
            self.timestamp = int(float(timestamp))
        else:
            self.timestamp = time.time()

        assert isinstance(inputfiles, list)
        if all([ isinstance(x,CLAMInputFile) for x in inputfiles ]):
            self.inputfiles = [ (x.filename, x.metadata) for x in inputfiles ] #list of (filename, CLAMMetaData) objects of all input files
        else:
            assert all([ isinstance(x, tuple) and len(x) == 2 and isinstance(x[1], CLAMMetaData) for x in inputfiles ])
            self.inputfiles = inputfiles


    def xml(self, indent = ""):
        """Serialise provenance data to XML. This is included in CLAM Metadata files"""
        xml = indent + "<provenance type=\"clam\" id=\""+self.serviceid+"\" name=\"" +self.servicename+"\" url=\"" + self.serviceurl+"\" outputtemplate=\""+self.outputtemplate_id+"\" outputtemplatelabel=\""+self.outputtemplate_label+"\" timestamp=\""+str(self.timestamp)+"\">"
        for filename, metadata in self.inputfiles:
            xml += indent + " <inputfile name=\"" + clam.common.util.xmlescape(filename) + "\">"
            xml += metadata.xml(indent + " ") + "\n"
            xml += indent +  " </inputfile>\n"
        if self.parameters:
            xml += indent + " <parameters>\n"
            if isinstance(self.parameters, dict):
                parameters = self.parameters.values()
            elif isinstance(self.parameters, list):
                parameters = self.parameters
            for parameter in parameters:
                xml += parameter.xml(indent +"  ") + "\n"
            xml += indent + " </parameters>\n"
        xml += indent + "</provenance>"
        return xml

    @staticmethod
    def fromxml(node):
        """Return a CLAMProvenanceData instance from the given XML description. Node can be a string or an lxml.etree._Element."""
        if not isinstance(node,ElementTree._Element): #pylint: disable=protected-access
            node = parsexmlstring(node)
        if node.tag == 'provenance': #pylint: disable=too-many-nested-blocks
            if node.attrib['type'] == 'clam':
                serviceid = node.attrib['id']
                servicename = node.attrib['name']
                serviceurl = node.attrib['url']
                timestamp = node.attrib['timestamp']
                outputtemplate = node.attrib['outputtemplate']
                outputtemplatelabel = node.attrib['outputtemplatelabel']
                inputfiles = []
                parameters = []
                for subnode in node:
                    if subnode.tag == 'inputfile':
                        filename = node.attrib['name']
                        metadata = None
                        for subsubnode in subnode:
                            if subsubnode.tag == 'CLAMMetaData':
                                metadata = CLAMMetaData.fromxml(subsubnode)
                                break
                        inputfiles.append( (filename, metadata) )
                    elif subnode.tag == 'parameters':
                        for subsubnode in subnode:
                            if subsubnode.tag in vars(clam.common.parameters):
                                parameters.append(vars(clam.common.parameters)[subsubnode.tag].fromxml(subsubnode))
                            else:
                                raise Exception("Expected parameter class '" + subsubnode.tag + "', but not defined!")
                return CLAMProvenanceData(serviceid,servicename,serviceurl,outputtemplate, outputtemplatelabel, inputfiles, parameters, timestamp)
            else:
                raise NotImplementedError





class CLAMMetaData(object):
    """A simple hash structure to hold arbitrary metadata"""
    attributes = None #if None, all attributes are allowed! Otherwise it should be a dictionary with keys corresponding to the various attributes and a list of values corresponding to the *maximally* possible settings (include False as element if not setting the attribute is valid), if no list of values are defined, set True if the attrbute is required or False if not. If only one value is specified (either in a list or not), then it will be 'fixed' metadata
    allowcustomattributes = True

    mimetype = "text/plain" #No mimetype by default
    schema = ""


    def __init__(self, file, **kwargs):
        """Create metadata for an instance of ``CLAMFile``

        * ``file`` - Instance of ``CLAMFile`` to which the metadata applies

        The keyword arguments express key/value pairs that constitute the metadata. Special keyword arguments are:

        * ``provenance`` - An instance ``CLAMProvenanceData``
        * ``inputtemplate`` - A string containing the ID of the input template

        CLAMMetaData acts like a dictionary in many regards.

        """

        if isinstance(file, CLAMFile):
            self.file = file
        elif file is None:
            self.file = None
        else:
            raise Exception("Invalid file argument for CLAMMetaData")



        self.file = file #will be used for reading inline metadata, can be None if no file is associated
        if self.file:
            self.file.metadata = self

        self.provenance = None

        self.inputtemplate = None

        self.data = {}
        self.loadinlinemetadata()
        for key, value in kwargs.items():
            if key == 'provenance':
                assert isinstance(value, CLAMProvenanceData)
                self.provenance = value
            elif key == 'inputtemplate':
                if isinstance(value, InputTemplate):
                    self.inputtemplate = value.id
                else:
                    self.inputtemplate = value
            else:
                self[key] = value
        if self.attributes:
            if not self.allowcustomattributes:
                for key, value in kwargs.items():
                    if key not in self.attributes: #pylint: disable=unsupported-membership-test
                        raise KeyError("Invalid attribute '" + key + " specified. But this format does not allow custom attributes. (format: " + self.__class__.__name__ + ", file: " + str(file) + ")")

            for key, valuerange in self.attributes.items():
                if isinstance(valuerange,list):
                    if not key in self and not False in valuerange :
                        raise ValueError("Required metadata attribute " + key +  " not specified")
                    elif self[key] not in valuerange:
                        raise ValueError("Attribute assignment " + key +  "=" + self[key] + " has an invalid value, choose one of: " + " ".join(self.attributes[key])) + " (format: " + self.__class__.__name__ + ", file: " + str(file) + ")" #pylint: disable=unsubscriptable-object
                elif valuerange is False: #Any value is allowed, and this attribute is not required
                    pass #nothing to do
                elif valuerange is True: #Any value is allowed, this attribute is *required*
                    if not key in self:
                        raise ValueError("Required metadata attribute " + key +  " not specified (format: " + self.__class__.__name__ + ", file: " + str(file) + ")" )
                elif valuerange: #value is a single specific unconfigurable value
                    self[key] = valuerange

    def __getitem__(self, key):
        """Retrieve a metadata field"""
        return self.data[key]

    def __contains__(self, key):
        """Check is a metadata field exists"""
        return key in self.data

    def items(self):
        """Returns all items as (key, value) tuples"""
        return self.data.items()

    def __iter__(self):
        """Iterate over all (key, value) tuples"""
        return iter(self.data)

    def __setitem__(self, key, value):
        """Set a metadata field to a specific value"""
        if self.attributes is not None and not key in self.attributes: #pylint: disable=unsupported-membership-test
            if not self.allowcustomattributes:
                raise KeyError("Trying to set metadata field '" + key + "', but no custom attributes are allowed by the format")
        elif self.attributes and key in self.attributes: #pylint: disable=unsupported-membership-test
            maxvalues = self.attributes[key] #pylint: disable=unsubscriptable-object
            if isinstance(maxvalues, list):
                if not value in maxvalues:
                    raise ValueError("Invalid value '" + str(value) + "' for metadata field '" + key + "'")

        assert not isinstance(value, list)
        self.data[key] = value

    def xml(self, indent = ""):
        """Render an XML representation of the metadata""" #(independent of web.py for support in CLAM API)
        if not indent:
            xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        else:
            xml = ""
        xml += indent + "<CLAMMetaData format=\"" + self.__class__.__name__ + "\""
        if self.mimetype:
            xml += " mimetype=\""+self.mimetype+"\""
        if self.schema:
            xml += " schema=\""+self.schema+"\""
        if self.inputtemplate:
            xml += " inputtemplate=\""+self.inputtemplate+"\""
        xml += ">\n"

        for key, value in self.data.items():
            xml += indent + "  <meta id=\""+clam.common.util.xmlescape(key)+"\">"+clam.common.util.xmlescape(str(value))+"</meta>\n"

        if self.provenance:
            xml += self.provenance.xml(indent + "  ")

        xml += indent +  "</CLAMMetaData>"
        return xml

    def save(self, filename):
        """Save metadata to XML file"""
        with io.open(filename,'w',encoding='utf-8') as f:
            f.write(self.xml())

    def validate(self):
        """Validate the metadata"""
        #Should be overridden by subclasses
        return True

    def loadinlinemetadata(self):
        """Not implemented"""
        #Read inline metadata, can be overridden by subclasses
        pass

    def saveinlinemetadata(self):
        """Not implemented"""
        #Save inline metadata, can be overridden by subclasses
        pass

    @staticmethod
    def fromxml(node, file=None):
        """Read metadata from XML. Static method returning an CLAMMetaData instance (or rather; the appropriate subclass of CLAMMetaData) from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element): #pylint: disable=protected-access
            node = parsexmlstring(node)
        if node.tag == 'CLAMMetaData':
            dataformat = node.attrib['format']

            formatclass = None
            for C in CUSTOM_FORMATS: #CUSTOM_FORMATS will be injected by clamservice.py
                if C.__name__ == dataformat:
                    formatclass = C
                    break
            if formatclass is None and dataformat in vars(clam.common.formats) and issubclass(vars(clam.common.formats)[dataformat], CLAMMetaData):
                formatclass = vars(clam.common.formats)[dataformat]
            if formatclass is None:
                raise Exception("Format class " + dataformat + " not found!")

            data = {}
            if 'inputtemplate' in node.attrib:
                data['inputtemplate'] = node.attrib['inputtemplate']
            if 'inputtemplatelabel' in node.attrib:
                data['inputtemplatelabel'] = node.attrib['inputtemplatelabel']



            for subnode in node:
                if subnode.tag == 'meta':
                    key = subnode.attrib['id']
                    value = subnode.text
                    data[key] = value
                elif subnode.tag == 'provenance':
                    data['provenance'] = CLAMProvenanceData.fromxml(subnode)
            return formatclass(file, **data)
        else:
            raise Exception("Invalid CLAM Metadata!")

    def httpheaders(self):
        """HTTP headers to output for this format. Yields (key,value) tuples. Should be overridden in sub-classes!"""
        yield ("Content-Type", self.mimetype)

class CMDIMetaData(CLAMMetaData):
    """Direct CMDI Metadata support, not implemented yet, reserved for future use"""
    #MAYBE TODO LATER: implement
    pass


class InputTemplate(object):
    """This class represents an input template. A slot with a certain format and function to which input files can be uploaded"""

    def __init__(self, template_id, formatclass, label, *args, **kwargs):
        assert issubclass(formatclass, CLAMMetaData)
        assert not '/' in template_id and not '.' in template_id
        self.formatclass = formatclass
        self.id = template_id
        self.label = label

        self.parameters = []
        self.converters = []
        self.viewers = [] #MAYBE TODO Later: Support viewers in InputTemplates?
        self.inputsources = []

        self.unique = True #may mark input/output as unique

        self.optional = False #Output templates that are derived from optional Input Templates are conditional on the optional input file being presented!

        self.filename = None
        self.extension = None
        self.onlyinputsource = False #Use only the input sources
        self.acceptarchive = False #Accept and auto-extract archives

        for key, value in kwargs.items():
            if key == 'unique':
                self.unique = bool(value)
            elif key == 'multi':
                self.unique = not bool(value)
            elif key == 'optional':
                self.optional = bool(value)
            elif key == 'filename':
                self.filename = value # use '#' to insert a number in multi mode (will happen server-side!)
            elif key == 'extension':
                if value[0] == '.': #without dot
                    self.extension = value[1:]
                else:
                    self.extension = value
            elif key == 'acceptarchive':
                self.acceptarchive = bool(value)
            elif key == 'onlyinputsource':
                self.onlyinputsource = bool(value)
            else:
                raise ValueError("Unexpected keyword argument for InputTemplate: " + key)

        if not self.unique and (self.filename and not '#' in self.filename):
            raise Exception("InputTemplate configuration error for inputtemplate '" + self.id + "', filename is set to a single specific name, but unique is disabled. Use '#' in filename, which will automatically resolve to a number in sequence.")
        if self.unique and self.acceptarchive:
            raise Exception("InputTemplate configuration error for inputtemplate '" + self.id + "', acceptarchive demands multi=True")


        for arg in args:
            if isinstance(arg, clam.common.parameters.AbstractParameter):
                self.parameters.append(arg)
            elif isinstance(arg, clam.common.converters.AbstractConverter):
                self.converters.append(arg)
            elif isinstance(arg, clam.common.viewers.AbstractViewer):
                self.viewers.append(arg)
            elif isinstance(arg, InputSource):
                self.inputsources.append(arg)
            elif arg is None:
                pass
            else:
                raise ValueError("Unexpected parameter for InputTemplate " + id + ", expecting Parameter, Converter, Viewer or InputSource.")

        if self.onlyinputsource and not self.inputsources:
            raise Exception("No input sources defined for input template " + id + ", but onlyinputsource=True")

    def xml(self, indent = ""):
        """Produce Template XML"""
        xml = indent + "<InputTemplate id=\""+self.id+"\" format=\"" + self.formatclass.__name__ + "\"" + " label=\"" + self.label + "\""
        if self.formatclass.mimetype:
            xml +=" mimetype=\""+self.formatclass.mimetype+"\""
        if self.formatclass.schema:
            xml +=" schema=\""+self.formatclass.schema+"\""
        if self.filename:
            xml +=" filename=\""+self.filename+"\""
        if self.extension:
            xml +=" extension=\""+self.extension+"\""
        if self.optional:
            xml +=" optional=\"yes\""
        else:
            xml +=" optional=\"no\""
        if self.unique:
            xml +=" unique=\"yes\""
        else:
            xml +=" unique=\"no\""
        if self.acceptarchive:
            xml +=" acceptarchive=\"yes\""
        else:
            xml +=" acceptarchive=\"no\""
        xml += ">\n"
        for parameter in self.parameters:
            xml += parameter.xml(indent+"    ") + "\n"
        if self.converters:
            for converter in self.converters:
                xml += indent + "    <converter id=\""+converter.id+"\">"+clam.common.util.xmlescape(converter.label)+"</converter>\n"
        if self.inputsources:
            for inputsource in self.inputsources:
                xml += inputsource.xml(indent+"    ")
        xml += indent + "</InputTemplate>"
        return xml

    @staticmethod
    def fromxml(node):
        """Static method returning an InputTemplate instance from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element): #pylint: disable=protected-access
            node = parsexmlstring(node)
        assert node.tag.lower() == 'inputtemplate'

        template_id = node.attrib['id']
        dataformat = node.attrib['format']
        label = node.attrib['label']
        kwargs = {}
        if 'filename' in node.attrib:
            kwargs['filename'] = node.attrib['filename']
        if 'extension' in node.attrib:
            kwargs['extension'] = node.attrib['extension']
        if 'unique' in node.attrib:
            kwargs['unique'] =  node.attrib['unique'].lower() == 'yes' or node.attrib['unique'].lower() == 'true' or node.attrib['unique'].lower() == '1'
        if 'acceptarchive' in node.attrib:
            kwargs['acceptarchive'] = node.attrib['acceptarchive'].lower() == 'yes' or node.attrib['acceptarchive'].lower() == 'true' or node.attrib['acceptarchive'].lower() == '1'

        #find formatclass
        formatcls = None
        for C in CUSTOM_FORMATS: #CUSTOM_FORMATS will be injected by clamservice.py
            if C.__name__ == dataformat:
                formatcls = C
                break
        if formatcls is None:
            if dataformat in vars(clam.common.formats):
                formatcls = vars(clam.common.formats)[dataformat]
            else:
                raise Exception("Expected format class '" + dataformat+ "', but not defined!")

        args = []
        for subnode in node:
            if subnode.tag in vars(clam.common.parameters):
                args.append(vars(clam.common.parameters)[subnode.tag].fromxml(subnode))
            elif subnode.tag == 'converter':
                pass #MAYBE TODO: Reading converters from XML is not implemented (and not necessary at this stage)
            elif subnode.tag == 'viewer':
                pass #MAYBE TODO: Reading viewers from XML is not implemented (and not necessary at this stage)
            elif subnode.tag == 'inputsource':
                pass #MAYBE TODO: Reading input sources from XML is not implemented (and not necessary at this stage)
            else:
                raise Exception("Expected parameter class '" + subnode.tag + "', but not defined!")

        return InputTemplate(template_id,formatcls,label, *args, **kwargs)



    def json(self):
        """Produce a JSON representation for the web interface"""
        d = { 'id': self.id, 'format': self.formatclass.__name__,'label': self.label, 'mimetype': self.formatclass.mimetype,  'schema': self.formatclass.schema }
        if self.unique:
            d['unique'] = True
        if self.filename:
            d['filename'] = self.filename
        if self.extension:
            d['extension'] = self.extension
        if self.acceptarchive:
            d['acceptarchive'] = self.acceptarchive
        #d['parameters'] = {}

        #The actual parameters are included as XML, and transformed by clam.js using XSLT (parameter.xsl) to generate the forms
        parametersxml = ''
        for parameter in self.parameters:
            parametersxml += parameter.xml()
        d['parametersxml'] = '<?xml version="1.0" encoding="utf-8" ?><parameters>' + parametersxml + '</parameters>'
        d['converters'] = [ {'id':x.id, 'label':x.label} for x in self.converters ]
        d['inputsources'] = [ {'id':x.id, 'label':x.label} for x in self.inputsources ]

        return json.dumps(d)

    def __eq__(self, other):
        if isinstance(other, str) or (sys.version < '3' and isinstance(other,unicode)): #pylint: disable=undefined-variable
            return self.id == other
        else: #object
            return other.id == self.id

    def match(self, metadata, user = None):
        """Does the specified metadata match this template? returns (success,metadata,parameters)"""
        assert isinstance(metadata, self.formatclass)
        return self.generate(metadata,user)

    def matchingfiles(self, projectpath):
        """Checks if the input conditions are satisfied, i.e the required input files are present. We use the symbolic links .*.INPUTTEMPLATE.id.seqnr to determine this. Returns a list of matching results (seqnr, filename, inputtemplate)."""
        results = []

        if projectpath[-1] == '/':
            inputpath = projectpath + 'input/'
        else:
            inputpath = projectpath + '/input/'

        for linkf,realf in clam.common.util.globsymlinks(inputpath + '/.*.INPUTTEMPLATE.' + self.id + '.*'):
            seqnr = int(linkf.split('.')[-1])
            results.append( (seqnr, realf[len(inputpath):], self) )
        results = sorted(results)
        if self.unique and len(results) != 1:
            return []
        else:
            return results



    def validate(self, postdata, user = None):
        """Validate posted data  against the inputtemplate"""
        clam.common.util.printdebug("Validating inputtemplate " + self.id + "...")
        errors, parameters, _  = processparameters(postdata, self.parameters, user)
        return errors, parameters




    def generate(self, file, validatedata = None,  inputdata=None, user = None):
        """Convert the template into instantiated metadata, validating the data in the process and returning errors otherwise. inputdata is a dictionary-compatible structure, such as the relevant postdata. Return (success, metadata, parameters), error messages can be extracted from parameters[].error. Validatedata is a (errors,parameters) tuple that can be passed if you did validation in a prior stage, if not specified, it will be done automatically."""

        metadata = {}

        if not validatedata:
            assert inputdata
            errors, parameters = self.validate(inputdata,user) #pylint: disable=unused-variable
        else:
            errors, parameters = validatedata #pylint: disable=unused-variable

        #scan errors and set metadata
        success = True
        for parameter in parameters:
            assert isinstance(parameter, clam.common.parameters.AbstractParameter)
            if parameter.error:
                success = False
            else:
                metadata[parameter.id] = parameter.value

        if not success:
            metadata = None
        else:
            try:
                metadata = self.formatclass(file, **metadata)
            except:
                raise

        return success, metadata, parameters


class AbstractMetaField(object): #for OutputTemplate only
    """This abstract class is the basis for derived classes representing metadata fields of particular types. A metadata field is in essence a (key, value) pair. These classes are used in output templates (described by the XML tag ``meta``). They are not used by ``CLAMMetaData``"""

    def __init__(self,key,value=None):
        self.key = key
        self.value = value

    def xml(self, operator='set', indent = ""):
        """Serialize the metadata field to XML"""
        xml = indent + "<meta id=\"" + self.key + "\""
        if operator != 'set':
            xml += " operator=\"" + operator + "\""
        if not self.value:
            xml += " />"
        else:
            xml += ">" + self.value + "</meta>"
        return xml

    @staticmethod
    def fromxml(node):
        """Static method returning an MetaField instance (any subclass of AbstractMetaField) from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element): #pylint: disable=protected-access
            node = parsexmlstring(node)
        if node.tag.lower() != 'meta':
            raise Exception("Expected meta tag but got '" + node.tag + "' instead")

        key = node.attrib['id']
        if node.text:
            value = node.text
        else:
            value = None
        operator = 'set'
        if 'operator' in node.attrib:
            operator= node.attrib['operator']
        if operator == 'set':
            cls = SetMetaField
        elif operator == 'unset':
            cls = UnsetMetaField
        elif operator == 'copy':
            cls = CopyMetaField
        elif operator == 'parameter':
            cls = ParameterMetaField
        return cls(key, value)


    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        #in most cases we're only interested in 'data'
        raise Exception("Always override this method in inherited classes! Return True if data is modified, False otherwise")


class SetMetaField(AbstractMetaField):
    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        data[self.key] = self.value
        return True

    def xml(self, indent=""):
        return super(SetMetaField,self).xml('set', indent)

class UnsetMetaField(AbstractMetaField):
    def xml(self, indent = ""):
        return super(UnsetMetaField,self).xml('unset', indent)

    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        if self.key in data and (not self.value or (self.value and data[self.key] == self.value)):
            del data[self.key]
            return True
        return False

class CopyMetaField(AbstractMetaField):
    """In CopyMetaField, the value is in the form of templateid.keyid, denoting where to copy from. If not keyid but only a templateid is
    specified, the keyid of the metafield itself will be assumed."""

    def xml(self, indent = ""):
        return super(CopyMetaField,self).xml('copy', indent)

    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        raw = self.value.split('.')
        if len(raw) == 1:
            copytemplate = raw[0]
            copykey = self.key
        elif len(raw) == 2:
            copytemplate = raw[0]
            copykey = raw[1]
        else:
            raise Exception("Can't parse CopyMetaField value " + self.value)

        #find relevant inputfile
        edited = False
        for inputtemplate, f in relevantinputfiles:
            if inputtemplate.id == copytemplate:
                if f.metadata and copykey in f.metadata:
                    data[self.key] = f.metadata[copykey]
                    edited = True
        return edited

class ParameterMetaField(AbstractMetaField):
    def xml(self, indent=""):
        return super(ParameterMetaField,self).xml('parameter', indent)

    def resolve(self, data, parameters, parentfile, relevantinputfiles): #TODO: Verify
        if self.value in parameters:
            data[self.key] = parameters[self.value]
            return True
        else:
            return False

class OutputTemplate(object):
    def __init__(self, template_id, formatclass, label, *args, **kwargs):
        assert issubclass(formatclass, CLAMMetaData)
        assert '/' not in template_id and '.' not in template_id
        self.id = template_id
        self.formatclass = formatclass
        self.label = label

        self.viewers = []
        self.converters = []

        self.metafields = []
        for arg in args:
            if isinstance(arg, AbstractMetaField) or isinstance(arg,ParameterCondition):
                self.metafields.append(arg)
            elif isinstance(arg, clam.common.converters.AbstractConverter):
                self.converters.append(arg)
            elif isinstance(arg, clam.common.viewers.AbstractViewer):
                self.viewers.append(arg)
            elif arg is None:
                pass
            else:
                raise ValueError("Unexpected argument for OutputTemplate " + id + ", expecting MetaField, ParameterCondition, Viewer or Converter")


        self.unique = True #mark input/output as unique, as opposed to multiple files

        self.filename = None
        self.extension = None

        self.removeextensions = [] #Remove extensions

        self.parent = None
        self.copymetadata = False #copy metadata from parent (if set)

        for key, value in kwargs.items():
            if key == 'unique':
                self.unique = bool(value)
            elif key == 'multi': #alias
                self.unique = not bool(value)
            elif key == 'filename':
                self.filename = value # use # to insert a number in multi mode
            elif key == 'removeextension' or key=='removeextensions':
                #remove the following extension(s) (prior to adding the extension specified)
                if value is True:
                    #will remove all (only 1 level though)
                    self.removeextensions = True #pylint: disable=redefined-variable-type
                elif value is False:
                    pass
                elif not isinstance(value,list):
                    self.removeextensions = [value]
                else:
                    self.removeextensions = value
            elif key == 'extension':
                if value[0] == '.':
                    self.extension = value[1:]
                else:
                    self.extension = value #Add the following extension
            elif key == 'parent':
                if isinstance(value, InputTemplate): value = value.id
                self.parent = value #The ID of an inputtemplate
            elif key == 'copymetadata':
                self.copymetadata = bool(value) #True by default
            elif key == 'viewers' or key == 'viewer':
                if isinstance(value, clam.common.viewers.AbstractViewer):
                    self.viewers = [value]
                elif isinstance(value, list) and all([isinstance(x, clam.common.viewers.AbstractViewer) for x in value]):
                    self.viewers = value
                else:
                    raise Exception("Invalid viewer specified!")
            else:
                raise ValueError("Unexpected keyword argument for OutputTemplate: " + key)


        if not self.unique and (self.filename and not '$SEQNR' in self.filename and not '#' in self.filename):
            raise Exception("OutputTemplate configuration error in outputtemplate '" + self.id + "', filename is set to a single specific name, but unique is disabled. Use '$SEQNR' in filename, which will automatically resolve to a number in sequence.")


    def xml(self, indent = ""):
        """Produce Template XML"""
        xml = indent + "<OutputTemplate id=\"" + self.id + "\" format=\"" + self.formatclass.__name__ + "\"" + " label=\"" + self.label + "\""
        if self.formatclass.mimetype:
            xml +=" mimetype=\""+self.formatclass.mimetype+"\""
        if self.formatclass.schema:
            xml +=" schema=\""+clam.common.util.xmlescape(self.formatclass.schema)+"\""
        if self.filename:
            xml +=" filename=\""+clam.common.util.xmlescape(self.filename)+"\""
        if self.extension:
            xml +=" extension=\""+clam.common.util.xmlescape(self.extension)+"\""
        if self.parent:
            xml +=" parent=\""+clam.common.util.xmlescape(self.parent)+"\""
        if self.unique:
            xml +=" unique=\"yes\""
        else:
            xml +=" unique=\"no\""
        xml += ">\n"
        for metafield in self.metafields:
            xml += metafield.xml(indent + "    ") + "\n"

        xml += indent + "</OutputTemplate>"
        return xml

    @staticmethod
    def fromxml(node):
        """Static method return an OutputTemplate instance from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element): #pylint: disable=protected-access
            node = parsexmlstring(node)
        assert node.tag.lower() == 'outputtemplate'

        template_id = node.attrib['id']
        dataformat = node.attrib['format']
        label = node.attrib['label']
        kwargs = {}
        if 'filename' in node.attrib:
            kwargs['filename'] = node.attrib['filename']
        if 'extension' in node.attrib:
            kwargs['extension'] = node.attrib['extension']
        if 'unique' in node.attrib:
            kwargs['unique'] = node.attrib['unique'].lower() == 'yes' or node.attrib['unique'].lower() == 'true' or node.attrib['unique'].lower() == '1'
        if 'parent' in node.attrib:
            kwargs['parent'] = node.attrib['parent']

        #find formatclass
        formatcls = None
        for C in CUSTOM_FORMATS: #CUSTOM_FORMATS will be injected by clamservice.py
            if C.__name__ == dataformat:
                formatcls = C
                break
        if formatcls is None:
            if dataformat in vars(clam.common.formats):
                formatcls = vars(clam.common.formats)[dataformat]
            else:
                raise Exception("Specified format not defined! (" + dataformat + ")")

        args = []
        for subnode in node:
            if subnode.tag == 'parametercondition':
                args.append(ParameterCondition.fromxml(subnode))
            elif subnode.tag == 'converter':
                pass #MAYBE TODO: Reading converters from XML is not implemented (and not necessary at this stage)
            elif subnode.tag == 'viewer':
                pass #MAYBE TODO: Reading viewers from XML is not implemented (and not necessary at this stage)
            else:
                args.append(AbstractMetaField.fromxml(subnode))

        return OutputTemplate(template_id,formatcls,label, *args, **kwargs)



    def __eq__(self, other):
        return other.id == self.id

    def findparent(self, inputtemplates):
        """Find the most suitable parent, that is: the first matching unique/multi inputtemplate"""
        for inputtemplate in inputtemplates:
            if self.unique == inputtemplate.unique:
                return inputtemplate.id
        return None

    def getparent(self, profile):
        """Resolve a parent ID"""
        assert self.parent
        for inputtemplate in profile.input:
            if inputtemplate == self.parent:
                return inputtemplate
        raise Exception("Parent InputTemplate '"+self.parent+"' not found!")

    def generate(self, profile, parameters, projectpath, inputfiles, provenancedata=None):
        """Yields (inputtemplate, inputfilename, outputfilename, metadata) tuples"""

        project = os.path.basename(projectpath)

        if self.parent: #pylint: disable=too-many-nested-blocks
            #We have a parent, infer the correct filename

            #copy filename from parent
            parent = self.getparent(profile)

            #get input files for the parent InputTemplate
            parentinputfiles = parent.matchingfiles(projectpath)
            if not parentinputfiles:
                raise Exception("OutputTemplate '"+self.id + "' has parent '" + self.parent + "', but no matching input files were found!")

            #Do we specify a full filename?
            for seqnr, inputfilename, inputtemplate in parentinputfiles: #pylint: disable=unused-variable

                if self.filename:
                    filename = self.filename
                    parentfile = CLAMInputFile(projectpath, inputfilename)
                elif parent:
                    filename = inputfilename
                    parentfile = CLAMInputFile(projectpath, inputfilename)
                else:
                    raise Exception("OutputTemplate '"+self.id + "' has no parent nor filename defined!")

                #Make actual CLAMInputFile objects of ALL relevant input files, that is: all unique=True files and all unique=False files with the same sequence number
                relevantinputfiles = []
                for seqnr2, inputfilename2, inputtemplate2 in inputfiles:
                    if seqnr2 == 0 or seqnr2 == seqnr:
                        relevantinputfiles.append( (inputtemplate2, CLAMInputFile(projectpath, inputfilename2)) )

                #resolve # in filename (done later)
                #if not self.unique:
                #    filename.replace('#',str(seqnr))

                if not self.filename and self.removeextensions:
                    #Remove unwanted extensions
                    if self.removeextensions is True:
                        #Remove any and all extensions
                        filename = filename.split('.')[0]
                    elif isinstance(self.removeextensions, list):
                        #Remove specified extension
                        for ext in self.removeextensions:
                            if ext:
                                if ext[0] != '.' and filename[-len(ext) - 1:] == '.' + ext:
                                    filename = filename[:-len(ext) - 1]
                                elif ext[0] == '.' and filename[-len(ext):] == ext:
                                    filename = filename[:-len(ext)]


                if self.extension and not self.filename and filename[-len(self.extension) - 1:] != '.' + self.extension: #(also prevents duplicate extensions)
                    filename += '.' + self.extension


                #Now we create the actual metadata
                metadata = self.generatemetadata(parameters, parentfile, relevantinputfiles, provenancedata)

                #Resolve filename
                filename = resolveoutputfilename(filename, parameters, metadata, self, seqnr, project, inputfilename)

                yield inputtemplate, inputfilename, filename, metadata

        elif self.unique and self.filename:
            #outputtemplate has no parent, but specified a filename and is unique, this implies it is not dependent on input files:

            metadata = self.generatemetadata(parameters, None, [], provenancedata)

            filename = resolveoutputfilename(self.filename, parameters, metadata, self, 0, project, None)

            yield None, None, filename, metadata
        else:
            raise Exception("Unable to generate from OutputTemplate, no parent or filename specified")


    def generatemetadata(self, parameters, parentfile, relevantinputfiles, provenancedata = None):
        """Generate metadata, given a filename, parameters and a dictionary of inputdata (necessary in case we copy from it)"""
        assert isinstance(provenancedata,CLAMProvenanceData) or provenancedata is None

        data = {}

        if self.copymetadata:
            #Copy parent metadata
            for key, value in parentfile.metadata.items():
                data[key] = value

        for metafield in self.metafields:
            if isinstance(metafield, ParameterCondition):
                metafield = metafield.evaluate(parameters)
                if not metafield:
                    continue
            assert isinstance(metafield, AbstractMetaField)
            metafield.resolve(data, parameters, parentfile, relevantinputfiles)

        if provenancedata:
            data['provenance'] = provenancedata

        return self.formatclass(None, **data)






class ParameterCondition(object):
    def __init__(self, **kwargs):
        if 'then' not in kwargs:
            raise Exception("No 'then=' specified!")

        self.then = None
        self.otherwise = None

        self.conditions = []
        self.disjunction = False

        for key, value in kwargs.items():
            if key == 'then':
                if isinstance(value, OutputTemplate) or isinstance(value, InputTemplate) or isinstance(value, ParameterCondition) or isinstance(value, AbstractMetaField):
                    self.then = value
                elif value is None:
                    pass
                else:
                    raise Exception("Value of 'then=' must be InputTemplate, OutputTemplate or ParameterCondition!")
            elif key == 'else' or key == 'otherwise':
                if isinstance(value, OutputTemplate) or isinstance(value, InputTemplate) or isinstance(value, ParameterCondition) or isinstance(value, AbstractMetaField):
                    self.otherwise = value
                elif value is None:
                    pass
                else:
                    raise Exception("Value of 'else=' must be InputTemplate, OutputTemplate or ParameterCondition!")

            elif key == 'disjunction' or key == 'or':
                self.disjunction = value
            else:
                if key[-10:] == '_notequals':
                    self.conditions.append( (key[:-10], value,lambda x,y: x != y, 'notequals') )
                elif key[-12:] == '_greaterthan':
                    self.conditions.append( (key[:-12], value,lambda x,y: x != None and x != False and x > y, 'greaterthan') )
                elif key[-17:] == '_greaterequalthan':
                    self.conditions.append( (key[:-17],value, lambda x,y: x != None and x != False and x >= y, 'greaterequalthan') )
                elif key[-9:] == '_lessthan':
                    self.conditions.append( (key[:-9],value, lambda x,y: x != None and x != False and x < y , 'lessthan' ) )
                elif key[-14:] == '_lessequalthan':
                    self.conditions.append( (key[:-14], value,lambda x,y: x != None and x != False and x <= y, 'lessequalthan') )
                elif key[-9:] == '_contains':
                    self.conditions.append( (key[:-9], value,lambda x,y: x != None and x != False and y in x, 'contains') )
                elif key[-7:] == '_equals':
                    self.conditions.append( (key[:-7], value,lambda x,y: x != None and x == y, 'equals') )
                elif key[-4:] == '_set':
                    if value:
                        self.conditions.append( (key[:-4], value,lambda x,y: x, 'set') )
                    else:
                        self.conditions.append( (key[:-4], value,lambda x,y: not x, 'set') )
                else: #default is _equals
                    self.conditions.append( (key,value, lambda x,y: x != None and x == y,'equals') )

        if self.then is None:
            raise Exception("No then= specified for ParameterCondition!")

    def match(self, parameters):
        assert isinstance(parameters, dict)
        for key,refvalue,evalf,_ in self.conditions:
            if key in parameters:
                value = parameters[key].value
            else:
                value = None
            if evalf(value, refvalue):
                if self.disjunction:
                    return True
            else:
                if not self.disjunction: #conjunction
                    return False
        if self.disjunction:
            return False
        else:
            return True

    def allpossibilities(self):
        """Returns all possible outputtemplates that may occur (recusrively applied)"""
        l = []
        if isinstance(self.then, ParameterCondition):
            #recursive parametercondition
            l += self.then.allpossibilities()
        elif self.then:
            l.append(self.then)
        if self.otherwise:
            if isinstance(self.otherwise, ParameterCondition):
                l += self.otherwise.allpossibilities()
            else:
                l.append(self.otherwise)
        return l

    def evaluate(self, parameters):
        """Returns False if there's no match, or whatever the ParameterCondition evaluates to (recursively applied!)"""
        if self.match(parameters):
            if isinstance(self.then, ParameterCondition):
                #recursive parametercondition
                return self.then.evaluate(parameters)
            else:
                return self.then
        elif self.otherwise:
            if isinstance(self.otherwise, ParameterCondition):
                #recursive else
                return self.otherwise.evaluate(parameters)
            else:
                return self.otherwise
        return False

    def xml(self, indent = ""):
        xml = indent + "<parametercondition>\n" + indent + " <if>\n"
        for key, value, evalf, operator in self.conditions: #pylint: disable=unused-variable
            xml += indent + "  <" + operator + " parameter=\"" + key + "\">" + clam.common.util.xmlescape(str(value)) + "</" + operator + ">\n"
        xml += indent + " </if>\n" + indent + " <then>\n"
        xml += self.then.xml(indent + "    ") + "\n"
        xml += indent + " </then>\n"
        if self.otherwise:
            xml += indent + " <else>\n"
            xml += self.otherwise.xml(indent + "     ") + "\n"
            xml += indent + " </else>"
        xml += indent + "</parametercondition>"
        return xml

    @staticmethod
    def fromxml(node):
        """Static method returning a ParameterCondition instance from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element): #pylint: disable=protected-access
            node = parsexmlstring(node)
        assert node.tag.lower() == 'parametercondition'

        kwargs = {}

        found = False
        for node in node:
            if node.tag == 'if':
                #interpret conditions:
                for subnode in node:
                    operator = subnode.tag
                    parameter = subnode.attrib['parameter']
                    value = subnode.text
                    kwargs[parameter + '_' + operator] = value
                    found = True
            elif node.tag == 'then' or node.tag == 'else' or node.tag == 'otherwise':
                #interpret statements:
                for subnode in node: #MAYBE TODO LATER: Support for multiple statement in then=, else= ?
                    if subnode.tag.lower() == 'parametercondition':
                        kwargs[node.tag] = ParameterCondition.fromxml(subnode)
                    elif subnode.tag == 'meta':
                        #assume metafield?
                        kwargs[node.tag] = AbstractMetaField.fromxml(subnode)
                    elif subnode.tag.lower() == 'outputtemplate':
                        kwargs[node.tag] = OutputTemplate.fromxml(subnode)
        if not found:
            raise Exception("No condition found in ParameterCondition!")
        return ParameterCondition(**kwargs)

class InputSource(object):
    def __init__(self, **kwargs):
        if 'id' in kwargs:
            self.id = kwargs['id']
            del kwargs['id']
        else:
            raise Exception("No id specified for InputSource")
        if 'label' in kwargs:
            self.label = kwargs['label']
            del kwargs['label']
        else:
            raise Exception("No label specified for InputSource")

        if 'path' in kwargs:
            self.path = kwargs['path']
            del kwargs['path']
            if not os.path.exists(self.path):
                raise Exception("No such file or directory for InputSource: " + self.path)
        else:
            raise Exception("No path specified for InputSource")

        if 'defaultmetadata' in kwargs:
            self.metadata = kwargs['defaultmetadata']
            del kwargs['defaultmetadata']
            assert isinstance(self.metadata, CLAMMetaData)
        elif 'metadata' in kwargs: #alias
            self.metadata = kwargs['metadata']
            del kwargs['metadata']
            assert isinstance(self.metadata, CLAMMetaData)
        else:
            self.metadata = None

        if 'inputtemplate' in kwargs:
            self.inputtemplate = kwargs['inputtemplate']
            del kwargs['inputtemplate']
        else:
            self.inputtemplate = None

        for key in kwargs:
            raise ValueError("Invalid keyword argument for InputSource: " + key)




    def isfile(self):
        return os.path.isfile(self.path)


    def isdir(self):
        return os.path.isdir(self.path)


    def xml(self, indent = ""):
        return indent + "<inputsource id=\""+self.id+"\">"+self.label+"</inputsource>"

    def check(self):
        """Checks if this inputsource is usable in INPUTSOURCES"""
        if not self.inputtemplate:
            raise Exception("Input source has no input template")


class Action(object):
    def __init__(self, *args, **kwargs):
        if 'id' in kwargs:
            self.id = kwargs['id']
        else:
            raise Exception("No id specified for Action")

        if 'name' in kwargs:
            self.name = kwargs['name']
        else:
            self.name = self.id

        if 'description' in kwargs:
            self.description = kwargs['description']
        else:
            self.description = ""

        if 'command' in kwargs:
            self.command = kwargs['command']
            self.function = None
        elif 'function' in kwargs:
            self.command = None
            self.function = kwargs['function']
        else:
            self.command = self.function = None #action won't be able to do anything!


        if 'method' in kwargs:
            self.method = kwargs['method']
        else:
            self.method = None #all methods

        if 'parameters' in kwargs:
            assert all( [ isinstance(x, clam.common.parameters.AbstractParameter) for x in kwargs['parameters']  ])
            self.parameters = kwargs['parameters']
        elif args:
            assert all( [ isinstance(x, clam.common.parameters.AbstractParameter) for x in args  ])
            self.parameters = args
        else:
            self.parameters = [] #pylint: disable=redefined-type


        if 'mimetype' in kwargs:
            self.mimetype = kwargs['mimetype']
        else:
            self.mimetype = "text/plain"

        if 'returncodes404' in kwargs:
            self.returncodes404 = kwargs['returncodes404']
        else:
            self.returncodes404 = [4]

        if 'returncodes403' in kwargs:
            self.returncodes403 = kwargs['returncodes403']
        else:
            self.returncodes403 = [3]

        if 'returncodes200' in kwargs:
            self.returncodes200 = kwargs['returncodes200']
        else:
            self.returncodes200 = [0]


        if 'allowanonymous' in kwargs:
            self.allowanonymous = bool(kwargs['allowanonymous'])
        else:
            self.allowanonymous = False

        if 'tmpdir' in kwargs:
            self.tmpdir = kwargs['tmpdir']
        else:
            self.tmpdir = False



    def xml(self, indent = ""):
        if self.method:
            method = "method=\"" + self.method + "\""
        else:
            method = ""
        if self.allowanonymous:
            allowanonymous = "allowanoymous=\"yes\""
        else:
            allowanonymous = ""
        xml = indent + "<action id=\"" + self.id + "\" " + method + " name=\"" + self.name + "\" description=\"" +self.description + "\" mimetype=\"" + self.mimetype + "\" " + allowanonymous + ">\n"
        for parameter in self.parameters:
            xml += parameter.xml(indent+ "    ") + "\n"
        xml += indent + "</action>\n"
        return xml

    @staticmethod
    def fromxml(node):
        """Static method returning an Action instance from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element): #pylint: disable=protected-access
            node = parsexmlstring(node)
        assert node.tag.lower() == 'action'

        kwargs = {}
        args = []
        if 'id' in node.attrib:
            kwargs['id'] = node.attrib['id']
        elif 'name' in node.attrib:
            kwargs['name'] = node.attrib['name']
        elif 'description' in node.attrib:
            kwargs['description'] = node.attrib['description']
        elif 'method' in node.attrib:
            kwargs['method'] = node.attrib['method']
        elif 'mimetype' in node.attrib:
            kwargs['mimetype'] = node.attrib['mimetype']
        elif 'allowanonymous' in node.attrib:
            if node.attrib['allowanonymous'] == "yes":
                kwargs['allowanonymous'] = True

        found = False
        for subnode in node:
            if subnode.tag.lower() == 'parametercondition':
                kwargs[node.tag] = ParameterCondition.fromxml(subnode)
            elif subnode.tag in vars(clam.common.parameters):
                args.append(vars(clam.common.parameters)[subnode.tag].fromxml(subnode))
        if not found:
            raise Exception("No condition found in ParameterCondition!")
        return Action(*args, **kwargs)

class Forwarder(object):
    def __init__(self, id, name, url, description="", type='zip'):
        self.id = id
        self.name = name
        self.url = url
        self.description = description
        self.type = type

    def __call__(self, project, baseurl, outputfile=None):
        """Return the forward link given a project and (optionally) an outputfile. If no outputfile was selected, a link is generator to download the entire output archive."""
        if outputfile:
            self.forwardlink = self.url.replace("$BACKLINK", outputfile.filename)
        else:
            self.forwardlink =  self.url.replace("$BACKLINK", baseurl + '/' + project + '/output/' + self.type)
        return self



def resolveinputfilename(filename, parameters, inputtemplate, nextseq = 0, project = None):
    #parameters are local
    if filename.find('$') != -1:
        for parameter in sorted(parameters, key= lambda x: len(x.id),reverse=True):#cmp=lambda x,y: len(x.id) - len(y.id)):
            if parameter and parameter.hasvalue:
                filename = filename.replace('$' + parameter.id, str(parameter.value))
        if filename.find('$') != -1:
            if project: filename = filename.replace('$PROJECT', project)
            if not inputtemplate.unique: filename = filename.replace('$SEQNR', str(nextseq))

    #BACKWARD COMPATIBILITY:
    if not inputtemplate.unique:
        if '#' in filename: #resolve number in filename
            filename = filename.replace('#',str(nextseq))

    clam.common.util.printdebug("Determined input filename: " + filename)


    return filename

def resolveoutputfilename(filename, globalparameters, localparameters, outputtemplate, nextseq, project, inputfilename):
    #MAYBE TODO: make more efficient
    if filename.find('$') != -1:
        for parameter_id, parameter in sorted(globalparameters.items(), key=lambda x: len(x[0]),reverse=True): #, cmp=lambda x,y: len(y[0]) - len(x[0])):
            if parameter and parameter.hasvalue:
                filename = filename.replace('$' + parameter.id, str(parameter.value))
        if filename.find('$') != -1:
            for parameter_id, value in sorted(localparameters.items(), key=lambda x:len(x[0]),reverse=True): # cmp=lambda x,y: len(y[0]) - len(x[0])):
                if value != None:
                    filename = filename.replace('$' + parameter_id, str(value))
        if filename.find('$') != -1:
            if inputfilename:
                inputfilename = os.path.basename(inputfilename)
                raw = inputfilename.split('.',1)
                inputstrippedfilename = raw[0]
                if len(raw) > 1:
                    inputextension = raw[1]
                else:
                    inputextension = ""
                filename = filename.replace('$INPUTFILENAME', inputfilename)
                filename = filename.replace('$INPUTSTRIPPEDFILENAME', inputstrippedfilename)
                filename = filename.replace('$INPUTEXTENSION', inputextension)
            if project: filename = filename.replace('$PROJECT', project)
            if not outputtemplate.unique:
                filename = filename.replace('$SEQNR', str(nextseq))

    #BACKWARD COMPATIBILITY:
    if not outputtemplate.unique:
        if '#' in filename: #resolve number in filename
            filename = filename.replace('#',str(nextseq))

    clam.common.util.printdebug("Determined output filename: " + filename)

    return filename


def escape(s, quote):
    s2 = ""
    for i, c in enumerate(s):
        if c == quote:
            escapes = 0
            j = i - 1
            while j > 0:
                if s[j] == "\\":
                    escapes += 1
                else:
                    break
                j -= 1
            if escapes % 2 == 0: #even number of escapes, we need another one
                s2 += "\\"
        s2 += c
    return s2

def shellsafe(s, quote='', doescape=True):
    """Returns the value string, wrapped in the specified quotes (if not empty), but checks and raises an Exception if the string is at risk of causing code injection"""
    if sys.version[0] == '2' and not isinstance(s,unicode): #pylint: disable=undefined-variable
        s = unicode(s,'utf-8') #pylint: disable=undefined-variable
    if len(s) > 1024:
        raise ValueError("Variable value rejected for security reasons: too long")
    if quote:
        if quote in s:
            if doescape:
                s = escape(s,quote)
            else:
                raise ValueError("Variable value rejected for security reasons: " + s)
        return quote + s + quote
    else:
        for c in s:
            if c in DISALLOWINSHELLSAFE:
                raise ValueError("Variable value rejected for security reasons: " + s)
        return s

def escapeshelloperators(s):
    inquote = False
    indblquote = False
    o = ""
    for c in s:
        if c == "'" and not indblquote:
            inquote = not inquote
            o += c
        elif c == '"' and not inquote:
            indblquote = not indblquote
            o += c
        elif not inquote and not indblquote:
            if c == '|':
                o += '%PIPE%'
            elif c == '>':
                o +=  '%OUT%'
            elif c == '<':
                o += '%IN%'
            elif c == '&':
                o += '%AMP%'
            elif c == '!':
                o += '%EXCL%'
            else:
                o += c
        else:
            o += c
    return o

def unescapeshelloperators(s):
    if sys.version < '3':
        s = s.replace(b'%PIPE%',b'|')
        s = s.replace(b'%OUT%',b'>')
        s = s.replace(b'%AMP%',b'&')
        s = s.replace(b'%EXCL%',b'!')
        s = s.replace(b'%IN%',b'<')
    else:
        s = s.replace('%PIPE%','|')
        s = s.replace('%OUT%','>')
        s = s.replace('%AMP%','&')
        s = s.replace('%EXCL%','!')
        s = s.replace('%IN%','<')
    return s

def loadconfig(callername, required=True):
    try:
        settingsmodule = sys.modules[callername]
    except:
        raise ConfigurationError("Unable to determine caller module, got unknown name: " + callername)
    hostname = os.uname()[1]
    searchpath = []
    searchfile = []
    searchpath.append(os.getcwd())
    d = os.path.dirname(settingsmodule.__file__)
    if d:
        searchpath.append(d)
    if hasattr(settingsmodule, 'SYSTEM_ID'):
        searchfile.append(settingsmodule.SYSTEM_ID + '.' + hostname+'.yml')
        searchfile.append(settingsmodule.SYSTEM_ID + '.' + hostname+'.yaml')
        searchfile.append(settingsmodule.SYSTEM_ID + '.config.yml')
        searchfile.append(settingsmodule.SYSTEM_ID + '.config.yaml')
    searchfile.append(hostname+'.yml')
    searchfile.append(hostname+'.yaml')
    searchfile.append('config.yml')
    searchfile.append('config.yaml')
    configfile = None

    #search host-specific configuration
    if 'CONFIGFILE' in os.environ:
        if os.environ['CONFIGFILE'][0] == '/' or os.path.exists(os.environ['CONFIGFILE']):
            configfile = os.environ['CONFIGFILE']
        else:
            searchfile.insert(0, os.path.basename(os.environ['CONFIGFILE']))

    if not configfile:
        for filename in searchfile:
            for path in searchpath:
                if os.path.exists(os.path.join(path, filename)):
                    configfile = os.path.join(path, filename)
                    break
            if configfile: break
    if configfile:
        os.environ['CONFIGFILE'] = configfile #we need to set this so when clamdispatcher loads it can be found again!
        with io.open(configfile,'r', encoding='utf-8') as f:
            data = yaml.safe_load(f.read())
        for key, value in data.items():
            #replace variables
            if isinstance(value,str) and '{' in value:
                variables = re.findall(r"\{\{\w+\}\}", value)
                for v in variables:
                    if v.strip('{}') in os.environ:
                        value = value.replace(v,os.environ[v.strip('{}')])
                    else:
                        print("Undefined environment variable in " + configfile + ": " + v.strip('{}'),file=sys.stderr)
                        value = value.replace(v,"")
            setattr(settingsmodule,key.upper(), value)
        return True

    if required:
        raise ConfigurationError("Unable to load required external configuration file. Do you need to set the CONFIGFILE environment variable? Detected hostname is " + hostname + "; search path is " + ", ".join(searchpath) + "; searched for " + ", ".join(searchfile))
    else:
        return False


#yes, this is deliberately placed at the end!
import clam.common.formats #pylint: disable=wrong-import-position
