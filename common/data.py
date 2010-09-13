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
import urllib2
import os.path
import codecs


class FormatError(Exception):
     """This Exception is raised when the CLAM response is not in the valid CLAM XML format"""
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return "Not a valid CLAM XML response"

class CLAMFile:
    def __init__(self, projectpath, filename, format):
            self.remote = (projectpath[0:7] == 'http://' or projectpath[0:8] == 'https://')
            self.projectpath = projectpath
            self.filename = filename
            self.format = format


    def readlines(self):
        """Loads all in memory"""
        return list(iter(self))



class CLAMInputFile(CLAMFile):
    def __iter__(self):
        """Read the lines of the file, one by one"""
        if not self.remote:
            for line in codecs.open(self.projectpath + 'input/' + self.filename, 'r', self.format.encoding).readlines():
                yield line
        else:
            req = urllib2.urlopen(self.projectpath + 'input/' + self.filename)
            for line in req.readlines():
                yield line

    def validate(self):
        return self.format.validate('output/' + self.path)



    
class CLAMOutputFile(CLAMFile):
    def __iter__(self):
        """Read the lines of the file, one by one"""
        if not self.remote:
            for line in codecs.open(self.projectpath + 'output/' + self.filename, 'r', self.format.encoding).readlines():
                yield line
        else:
            req = urllib2.urlopen(self.projectpath + 'output/' + self.filename)
            for line in req.readlines():
                yield line

    def validate(self):
        return self.format.validate('output/' + self.path)

    def __str__(self):
        return self.projectpath + 'output/' + self.filename


def getclamdata(filename):
    """This function reads the CLAM Data from an XML file. Use this to read
    the clam.xml file from your system wrapper. It returns a CLAMData instance."""
    f = open(filename,'r')
    xml = f.read(os.path.getsize(filename))
    f.close()
    return CLAMData(xml)
    
    

class CLAMData(object):    
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

    def __init__(self, xml):
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

        self.parseresponse(xml)
        


    def parseresponse(self, xml):
        """The parser, there's usually no need to call this directly"""
        global VERSIONs
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
                self.projecturl = root.attrib['baseurl'] + '/' + self.project + '/'


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
                    if formatnode.tag == 'inputformat': 
                        self.inputformats.append( clam.common.formats.formatfromxml(formatnode) )
            elif node.tag == 'outputformats':        
                for formatnode in node:
                    if formatnode.tag == 'outputformat': 
                        self.outputformats.append( clam.common.formats.formatfromxml(formatnode) )
            elif node.tag == 'input':
                 for filenode in node:
                    if filenode.tag == 'path':
                        selectedformat = clam.common.formats.Format()
                        for format in self.inputformats: 
                            if unicode(format) == filenode.attrib['format']: #TODO: verify
                                selectedformat = format
                        self.input.append( CLAMInputFile( self.projecturl, filenode.text, selectedformat) )
            elif node.tag == 'output': 
                 for filenode in node:
                    if filenode.tag == 'path':
                        selectedformat = clam.common.formats.Format()
                        for format in self.outputformats: 
                            if unicode(format) == filenode.attrib['format']: #TODO: verify
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

