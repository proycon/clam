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

import codecs
import os.path
import httplib2
from urllib import urlencode


from clam.external.poster.encode import multipart_encode
from clam.external.poster.streaminghttp import register_openers



import clam.common.status
import clam.common.parameters
import clam.common.formats
from clam.common.data import CLAMData, CLAMInputFile, CLAMOutputFile

VERSION = 0.3


# Register poster's streaming http handlers with urllib2
register_openers()


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

class NoConnection(Exception):
         def __init__(self):
            pass
         def __str__(self):
            return "Can't establish a connection with the server" 



class CLAMClient:
    def __init__(self, url, user=None, password=None):
        self.http = httplib2.Http()
        if url[-1] != '/': url += '/'
        self.url = url
        if user and password:
            self.http.add_credentials(user, password)

    def request(self, url, method = 'GET', data = None):
        try:
            if data: 
                response, content = self.http.request(self.url + url, method, data)
            else:
                response, content = self.http.request(self.url + url, method)
        except:
            raise NoConnection()
        return self._parse(response, content)

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
                
   

 
    def index(self):
        """get index of projects"""
        return self.request('')

    def get(self, project):
        """query the project status"""
        return self.request(project + '/')

    def create(self,project):
        """create a new project"""
        return self.request(project + '/', 'PUT')
     

    def start(self, project, **parameters):
        """start a run"""
        auth = None
        if 'auth' in parameters:
            auth = parameters['auth']
            del parameters['auth']

        return self.request(project + '/', 'POST', urlencode(parameters))


    def delete(self,project)
        """aborts AND deletes a project"""
        return self.request(project + '/', 'DELETE')

    def abort(self, project): #alias
        return self.abort(project)


    def downloadarchive(self, project, targetfile, format = 'zip'):
        """download all output as archive"""
        #TODO: Redo
        req = urllib2.urlopen(self.url + project + '/output/?format=' + format) #TODO: Auth support
        CHUNK = 16 * 1024
        while True:
            chunk = req.read(CHUNK)
            if not chunk: break
            targetfile.write(chunk)


    def upload(self, project, file, format):
        """upload a file (or archive)"""
        #TODO: Adapt for new metadata scheme and httplib2
        # datagen is a generator object that yields the encoded parameters
        datagen, headers = multipart_encode({"file": file, 'uploadformat1': format.__class__.__name__})

        # Create the Request object
        request = urllib2.Request(self.url + project + '/upload/', datagen, headers)
        return urllib2.urlopen(request).read()

