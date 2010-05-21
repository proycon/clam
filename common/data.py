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
import os.path
import codecs


class FormatError(Exception):
         def __init__(self, value):
             self.value = value
         def __str__(self):
             return "Not a valid CLAM XML response"

class CLAMFile: #TODO: adapt for client versus server! (inputfile vs outputfile?)
    def __init__(self, path, format):
            self.path = path
            self.format = format

    def __str__(self):
        return self.path



        


class CLAMInputFile(CLAMFile):
    def open(self):
        """open the file for reading, only works within wrapper scripts!"""
        return codecs.open('input/' + self.path, 'r', self.format.encoding)

    def validate(self):
        return self.format.validate('input/' + self.path)

    
class CLAMOutputFile(CLAMFile):
    pass


def getclamdata(filename):
    f = open(filename,'r')
    xml = f.read(os.path.getsize(filename))
    f.close()
    return CLAMData(xml)
    
    

class CLAMData(object):    
    def __init__(self, xml):
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
                    if formatnode.tag == 'inputformat': #TODO
                        self.inputformats.append( clam.common.formats.formatfromxml(formatnode) )
            elif node.tag == 'outputformats':        
                for formatnode in node:
                    if formatnode.tag == 'outputformat': #TODO
                        self.outputformats.append( clam.common.formats.formatfromxml(formatnode) )
            elif node.tag == 'input':
                 for filenode in node:
                    if filenode.tag == 'path':
                        selectedformat = clam.common.formats.Format()
                        for format in self.inputformats: 
                            if unicode(format) == filenode.attrib['format']: #TODO: verify
                                selectedformat = format
                        self.input.append( CLAMInputFile( filenode.text, selectedformat) )
            elif node.tag == 'output': 
                 for filenode in node:
                    if filenode.tag == 'path':
                        selectedformat = clam.common.formats.Format()
                        for format in self.outputformats: 
                            if unicode(format) == filenode.attrib['format']: #TODO: verify
                                selectedformat = format
                        self.output.append( CLAMOutputFile( filenode.text, selectedformat) )
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
        """Return all parameters as id => value dictionary"""
        paramdict = {}
        for parametergroup, params in self.parameters:
            for parameter in params:
                if parameter.value:
                    if isinstance(parameter.value, list):
                        paramdict[parameter.id] = ",".join(parameter.value)
                    else:
                        paramdict[parameter.id] = parameter.value
        return paramdict

