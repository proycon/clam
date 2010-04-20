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

VERSION = 0.2

class FormatError(Exception):
         def __init__(self, value):
             self.value = value
         def __str__(self):
             return "Not a valid CLAM XML response"

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
        root = ElementTree.parse(StringIO(xml)).getroot()
        if root.tag != 'clam':
            raise FormatError()
        for node in root:
            if node.tag == 'parameters':
            elif node.tag == 'corpora':        
            elif node.tag == 'inputformats':        
            elif node.tag == 'outputformats':        
            elif node.tag == 'corpora':       
            elif node.tag == 'input':
            elif node.tag == 'output': 
                                      
 

class CLAMClient(object):
    def __init__(self,host, port):
        pass
    
