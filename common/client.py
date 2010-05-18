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
import codecs
import os.path
from httplib2 import Http
from urllib import urlencode

import clam.common.status
import clam.common.parameters
import clam.common.formats

VERSION = 0.2


class FormatError(Exception):
         def __init__(self, value):
             self.value = value
         def __str__(self):
             return "Not a valid CLAM XML response"

class BadRequest(Exception):
         def __init__(self):
            pass
         def __str__(self):
            return "Bad Request"

class NotFound(Exception):
         def __init__(self):
            pass
         def __str__(self):
            return "Not Found"

class PermissionDenied(Exception):
         def __init__(self):
            pass
         def __str__(self):
            return "Permission Denied"

class ServerError(Exception):
         def __init__(self):
            pass
         def __str__(self):
            return "Server Error"

class AuthRequired(Exception):
         def __init__(self):
            pass
         def __str__(self):
            return "Authorization Required"

class CLAMFile:
    def __init__(self, path, format):
            self.path = path
            self.format = format

    def open(self):
        return codecs.open(self.path, 'r', self.format.encoding)

    def validate(self):
        return self.format.validate(self.path)

    def __str__(self):
        return self.path

def getclamdata(filename):
    f = open(filename,'r')
    xml = f.read(os.path.getsize(filename))
    f.close()
    return CLAMData(xml)
    
    

class CLAMData(object):    
    def __init__(self, xml):
        self.status = clam.common.status.READY
        self.parameters = []
        self.inputformats = []
        self.outputformats = []
        self.corpora = []
        self.input = []
        self.output = []
        self.projects = None
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
                        selectedformat = None
                        for format in self.inputformats: 
                            if unicode(format) == filenode.attrib['format']: #TODO: verify
                                selectedformat = format
                        self.input.append( CLAMFile('input/' + filenode.text, selectedformat) )
            elif node.tag == 'output': 
                 for filenode in node:
                    if filenode.tag == 'path':
                        selectedformat = None
                        for format in self.outputformats: 
                            if unicode(format) == filenode.attrib['format']: #TODO: verify
                                selectedformat = format
                        self.input.append( CLAMFile('output/' + filenode.text, selectedformat) )
            elif node.tag == 'projects': 
                 self.projects = []
                 for projectnode in node:
                    if projectnode.tag == 'projects':
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

    def parameterdict(self):
        """Return all parameters as id => value dictionary"""
        paramdict = {}
        for parametergroup, params in parameters:
            for parameter in params:
                if parameter.value:
                    paramdict[parameter.id] = parameter.value
        return paramdict
        
 
class CLAMAuth:
    def __init__(self, user, password):
        pass



class CLAMClient:
    def __init__(self, url):
        self.http = Http()
        if url[-1] != '/': url += '/'
        self.url = url
        

    def _parse(self, response, content):
        if response['status'] == 200:
            return CLAMData(content)
        elif response['status'] == 400:
            raise BadRequest()
        elif response['status'] == 401:
            raise AuthRequired()
        elif response['status'] == 403:
            raise PermissionDenied()
        elif response['status'] == 404:
            raise NotFound()
                
    
    def index(self, auth = None):
        """get index of projects"""
        response, content = self.http.request(self.url)
        return self._parse(response, content)                    

    def get(self, project, auth = None):
        """query the project status"""
        response, content = self.http.request(self.url + project + '/')
        return self._parse(response, content)                    
    
    def create(self,project, auth = None):
        """create a new project"""
        response, content = self.http.request(self.url + project + '/','PUT')
        return self._parse(response, content)               

    def start(self, project, **parameters):
        """start a run"""
        auth = None
        if 'auth' in parameters:
            auth = parameters['auth']
            del parameters['auth']

        assert( isinstance(parameters, dict) )

        response, content = self.http.request(self.url + project + '/','POST', urlencode(parameters)) 
        return self._parse(response, content)                                     

    def abort(self,project, auth = None):
        """aborts AND deletes a project"""
        response, content = self.http.request(self.url + project + '/','DELETE') 
        return self._parse(response, content)               

    def downloadarchive(self, project, format = 'zip', auth = None):
        """download all output as archive"""
        pass

    def download(self, project, path, auth = None):
        """download one output file"""
        pass

    def upload(self, project, path, format, auth = None):
        """upload a file (or archive)"""
        pass


