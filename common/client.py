#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Client --
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

import common.status
import common.parameters
import common.formats

VERSION = 0.2

class FormatError(Exception):
         def __init__(self, value):
             self.value = value
         def __str__(self):
             return "Not a valid CLAM XML response"

class CLAMFile(object):
    def __init__(self, path, format):
            self.path = path
            self.format = format

    def open(self):
        pass #TODO

    def validate(self):
        pass #TODO        


class CLAMData(object):    
    def __init__(self, xml):
        self.status = common.status.READY
        self.parameters = []
        self.inputformats = []
        self.outputformats = []
        self.corpora = []
        self.input = []
        self.output = []
        self.parseresponse(xml)

    def parseresponse(self, xml):
        global VERSION
        root = ElementTree.parse(StringIO(xml)).getroot()
        if root.tag != 'clam':
            raise FormatError()
        if int(root.attribs['version']) > VERSION:
            raise Exception("The clam client version is too old!")

        for node in root:
            if node.tag == 'status':
                self.status = int(node.attribs['code'])
                self.statusmessage  = node.attribs['message']
            elif node.tag == 'parameters':
                for parametergroupnode in node:
                    if parametergroupnode.tag == 'parametergroup':
                        parameterlist = []
                        for parameternode in parametergroupnode:
                                parameterlist.append(common.parameters.parameterfromxml(parameternode))
                        self.parameters.append( (parametergroupnode.attribs['name'], parameterlist) )
            elif node.tag == 'corpora':
                for corpusnode in node:
                    if corpusnode.tag == 'corpus':
                        self.corpora.append(corpusnode.value)
            elif node.tag == 'inputformats':    
                for formatnode in node:
                    if formatnode.tag == 'inputformat': #TODO
                        self.inputformats.append( common.formats.formatfromxml(formatnode) )
            elif node.tag == 'outputformats':        
                for formatnode in node:
                    if formatnode.tag == 'outputformat': #TODO
                        self.outputformats.append( common.formats.formatfromxml(formatnode) )
            elif node.tag == 'input':
                 for filenode in node:
                    if node.tag == 'path':
                        selectedformat = None
                        for format in self.inputformats: 
                            if format.name == filenode.attribs['format']: #TODO: verify
                                selectedformat = format
                        self.input.append( CLAMFile(filenode.value, selectedformat) )
            elif node.tag == 'output': 
                 for filenode in node:
                    if node.tag == 'path':
                        selectedformat = None
                        for format in self.outputformats: 
                            if format.name == filenode.attribs['format']: #TODO: verify
                                selectedformat = format
                        self.input.append( CLAMFile(filenode.value, selectedformat) )
                                 
 

class CLAMClient(object):
    def __init__(self,host, port):
        pass
    
