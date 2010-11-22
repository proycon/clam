#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Data structures --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

from lxml import etree as ElementTree
from StringIO import StringIO
import clam.common.parameters
import clam.common.formats
import clam.common.metadata
import clam.common.util
import urllib2
import httplib2
import os.path
import codecs


class FormatError(Exception):
     """This Exception is raised when the CLAM response is not in the valid CLAM XML format"""
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return "Not a valid CLAM XML response"

class CLAMFile:
    basedir = ''
    
    def __init__(self, projectpath, filename, loadmetadata = True, user = None, password = None):
            """Create a CLAMFile object, providing immediate transparent access to CLAM Input and Output files, remote as well as local! And including metadata."""
            self.remote = (projectpath[0:7] == 'http://' or projectpath[0:8] == 'https://')
            self.projectpath = projectpath
            self.filename = filename
            self.metadata = None
            if loadmetadata:
                try:
                    self.loadmetadata()
                except IOError:
                    pass

            if self.remote:                
                self.http = httplib2.Http()
                if user and password:
                    self.http.add_credentials(user, password)
                
                
    def metafilename(self):
            """Returns the filename for the meta file (not full path). Only used for local files."""
            metafilename = os.path.dirname(self.filename) 
            if metafilename: metafilename += '/'
            metafilename += '.' + os.path.basename(self.filename) + '.METADATA'
            return metafilename
                
    def loadmetadata(self):
            if not self.remote:
                metafile = self.projectpath + self.basedir + '/' + self.metafilename()
                if os.path.exists(metafile):
                    f = open(metafile, 'r')
                    xml = "".join(f.readlines())
                    f.close()
                else:
                    raise IOError(2, "No metadata found!")
            else:
                try:
                    httpcode, xml = self.http.request(self.projectpath + self.basedir + '/' + self.filename + '/metadata')
                except:
                    raise IOError(2, "Can't download metadata!")
                
                if httpcode != 200: #TODO: Verify
                        raise IOError(2, "Can't download metadata!")
            
            #parse metadata
            self.metadata = clam.common.formats.getmetadatafromxml(self, xml) #returns CLAMMetaData object (or child thereof)
     
    def __iter__(self):
        """Read the lines of the file, one by one. This only works for local files, remote files are loaded into memory first (a httplib2 limitation)."""
        if not self.remote:
            if self.metadata and 'encoding' in self.metadata:
                for line in codecs.open(self.projectpath + self.basedir + '/' + self.filename, 'r', self.metadata['encoding']).readlines():
                    yield line
            else:
                for line in open(self.projectpath + self.basedir + '/' + self.filename, 'r').readlines():
                    yield line
        else:
            for line in self.readlines():
                yield line
        
            #TODO LATER: Re-add streaming support with urllib2? (But mind the digest authentication!)
            #req = self.opener(self.projectpath + basedir '/' + self.filename) #urllib2
            #for line in req.readlines():
            #    yield line
            #req.close()
    
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
            httpcode, content = self.http.request(self.projectpath + self.basedir + '/' + self.filename,'DELETE')
            return True
         

    def readlines(self):
        """Loads all in memory"""
        if not self.remote:
            if self.metadata and 'encoding' in self.metadata:
               return codecs.open(self.projectpath + self.basedir + '/' + self.filename, 'r', self.metadata['encoding']).readlines()
            else:
               return open(self.projectpath + self.basedir + '/' + self.filename, 'r').readlines()
        else:
            httpcode, content = self.http.request(self.projectpath + self.basedir + '/' + self.filename)
            return content
        

    def validate(self):
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

def getclamdata(filename):
    """This function reads the CLAM Data from an XML file. Use this to read
    the clam.xml file from your system wrapper. It returns a CLAMData instance."""
    f = open(filename,'r')
    xml = f.read(os.path.getsize(filename))
    f.close()
    return CLAMData(xml, True)
    
    

class CLAMData(object): #TODO: Adapt CLAMData for new metadata
    """Instances of this class hold all the CLAM Data that is automatically extracted from CLAM
    XML responses. Its member variables are: 

        status          - Contains any of clam.common.status.*
        statusmessage   - The latest status message (string)
        completion      - An integer between 0 and 100 indicating
                          the percentage towards completion.
        parameters      - List of parameters (but use the methods instead)
        inputformats    - List of all input formats
        outputformats   - List of all output formats
        corpora         - List of pre-installed corpora
        input           - List of input files  ([ CLAMInputFile ])
        output          - List of output files ([ CLAMOutputFile ])
        projects        - List of projects ([ string ])
        errors          - Boolean indicating whether there are errors in parameter specification
        errormsh        - String containing an error message

    Note that depending on the current status of the project, not all may be available.
    """

    def __init__(self, xml, localroot = False):
        """Pass an xml string containing the full response. It will be automatically parsed."""
        self.baseurl = ''
        self.projecturl = ''
        self.status = clam.common.status.READY
        self.statusmessage = ""
        self.completion = 0
        self.parameters = []
        self.inputformats = []
        self.outputformats = []
        self.corpora = []
        self.input = []
        self.output = []
        self.projects = None
        self.errors = False
        self.errormsg = ""

        self.parseresponse(xml, localroot)
        


    def parseresponse(self, xml, localroot = False):
        """The parser, there's usually no need to call this directly"""
        global VERSION
        root = ElementTree.parse(StringIO(xml)).getroot()
        if root.tag != 'clam':
            raise FormatError()
        #if float(root.attrib['version'][0:3]) > VERSION[0:3]:
        #    raise Exception("The clam client version is too old!")
        self.system_id = root.attrib['id']
        self.system_name = root.attrib['name']        
        if 'project' in root.attrib:
            self.project = root.attrib['project']
        else:
            self.project = None
        if 'baseurl' in root.attrib:
            self.baseurl = root.attrib['baseurl']
            if self.project:
                if localroot == True: #implicit, assume CWD
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

        for node in root:
            if node.tag == 'status':
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
                                parameterlist.append(clam.common.parameters.parameterfromxml(parameternode))
                        self.parameters.append( (parametergroupnode.attrib['name'], parameterlist) )
            elif node.tag == 'corpora':
                for corpusnode in node:
                    if corpusnode.tag == 'corpus':
                        self.corpora.append(corpusnode.value)
            elif node.tag == 'inputformats':    
                for formatnode in node:
                    self.inputformats.append( clam.common.formats.formatfromxml(formatnode) )
            elif node.tag == 'outputformats':        
                for formatnode in node:
                    self.outputformats.append( clam.common.formats.formatfromxml(formatnode) )
            elif node.tag == 'input':
                 for filenode in node:
                    if filenode.tag == 'path':
                        selectedformat = clam.common.formats.Format()
                        for format in self.inputformats: 
                            if format.__class__.__name__ == filenode.attrib['format']:
                                selectedformat = format
                        self.input.append( CLAMInputFile( self.projecturl, filenode.text, selectedformat) )
            elif node.tag == 'output': 
                 for filenode in node:
                    if filenode.tag == 'path':
                        selectedformat = clam.common.formats.Format()
                        for format in self.outputformats: 
                            if format.__class__.__name__ == filenode.attrib['format']:
                                selectedformat = format
                        self.output.append( CLAMOutputFile( self.projecturl, filenode.text, selectedformat) )
            elif node.tag == 'projects':
                 self.projects = []
                 for projectnode in node:
                    if projectnode.tag == 'project':
                        self.projects.append(projectnode.text)

    def parameter(self, id):                                 
        """Return the specified parameter"""
        for parametergroup, parameters in self.parameters:
            for parameter in parameters:
                if parameter.id == id:
                    return parameter
        raise KeyError

    def __getitem__(self, id):                                 
        """Return the specified parameter"""
        try:
            return self.parameter(id)
        except KeyError:
            raise

    def __setitem__(self, id, value):
        """Set the specified parameter"""
        for parametergroup, parameters in self.parameters:
            for parameter in parameters:
                if parameter.id == id:
                    parameter.set(value)
                    return True
        raise KeyError

    def passparameters(self):
        """Return all parameters as {id: value} dictionary"""
        paramdict = {}
        for parametergroup, params in self.parameters:
            for parameter in params:
                if parameter.value:
                    if isinstance(parameter.value, list):
                        paramdict[parameter.id] = ",".join(parameter.value)
                    else:
                        paramdict[parameter.id] = parameter.value
        return paramdict

