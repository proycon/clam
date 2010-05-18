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
from clam.common.data import CLAMData, CLAMFile

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

 
class CLAMAuth:
    def __init__(self, user, password):
        pass



class CLAMClient:
    def __init__(self, url):
        self.http = Http()
        if url[-1] != '/': url += '/'
        self.url = url
        

    def _parse(self, response, content):
        if response['status'] == '200':
            if content:
                return CLAMData(content)
            else:
                return True
        elif response['status'] == '400':
            raise BadRequest()
        elif response['status'] == '401':
            raise AuthRequired()
        elif response['status'] == '403':
            raise PermissionDenied()
        elif response['status'] == '404':
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
        self._parse(response, content)               

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


