#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Client --
#       by Maarten van Gompel (proycon)
#       http://proycon.github.com/clam
#
#       Centre for Language Studies
#       Radboud University Nijmegen
#
#       Induction for Linguistic Knowledge Research Group
#       Tilburg University
#
#       Licensed under GPLv3
#
###############################################################

from __future__ import print_function, unicode_literals, division, absolute_import

import os.path
import sys
import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor #pylint: disable=import-error
from lxml import etree as ElementTree
if sys.version < '3':
    from StringIO import StringIO #pylint: disable=import-error
    from io import IOBase
else:
    from io import StringIO, IOBase, BytesIO

import clam.common.status
import clam.common.parameters
import clam.common.formats
from clam.common.data import CLAMData, CLAMFile, CLAMInputFile, CLAMOutputFile, CLAMMetaData, InputTemplate, OutputTemplate, VERSION as DATAAPIVERSION, BadRequest, NotFound, PermissionDenied, ServerError, AuthRequired,NoConnection, UploadError, ParameterError, TimeOut, processhttpcode

VERSION = '0.99'
if VERSION != DATAAPIVERSION:
    raise Exception("Version mismatch beween Client API ("+clam.common.data.VERSION+") and Data API ("+DATAAPIVERSION+")!")


#for debug of requests:
#import logging
#logging.basicConfig(level=logging.DEBUG)

def donereadingupload(encoder):
    """Called when the uploaded file has been read"""
    #encoder.encoder.fields['file'][1].seek(0)
    pass

class CLAMClient:
    def __init__(self, url, user=None, password=None, oauth=False, oauth_access_token=None):
        """Initialise the CLAM client (does not actually connect yet)

        * ``url`` - URL of the webservice
        * ``user`` - username (or None if no authentication is needed or if using OAuth2)
        * ``password`` - password (or None if no authentication is needed or if using OAuth2)
        * ``oauth`` - Use OAuth2? (boolean)
        * ``oauth_access_token`` - OAuth2 Access Token (or None), if OAuth is
            enabled and no token is specified, the authorization provider will be called to obtain one.
            If this stage requires user interaction, it will fail.
        """

        #self.http = httplib2.Http()
        if url[-1] != '/': url += '/'
        self.url = url
        self.oauth = oauth
        self.oauth_access_token = oauth_access_token
        if user and password:
            self.authenticated = True
            self.user = user
            self.password = password
            self.oauth = False
            self.initauth()
        else:
            self.authenticated = False
            self.user = None
            self.password = None
            self.initauth()


    def initauth(self):
        """Initialise authentication, for internal use"""
        global VERSION

        headers = {'User-agent': 'CLAMClientAPI-' + VERSION}
        if self.oauth:
            if not self.oauth_access_token:
                r = requests.get(self.url,headers=headers)
                if r.status_code == 404:
                    raise NotFound("Authorization provider not found")
                elif r.status_code == 403:
                    raise PermissionDenied("Authorization provider denies access")
                elif not (r.status_code >= 200 and r.status_code <= 299):
                    raise Exception("An error occured, return code " + str(r.status_code))


                data = self._parse(r.text)
                if data is True: #indicates failure
                    raise Exception("No access token provided, but Authorization Provider requires manual user input. Unable to authenticate automatically. Obtain an access token from " + r.geturl())
                else:
                    self.oauth_access_token = data.oauth_access_token

            headers['Authorization'] = 'Bearer ' + self.oauth_access_token
        return headers



    def initrequest(self, data=None):
        params = {'headers': self.initauth() }
        if self.authenticated and not self.oauth:
           params['auth'] = requests.auth.HTTPDigestAuth(self.user, self.password)
        if data:
           params['data'] = data
        return params

    def request(self, url='', method = 'GET', data = None):
        """Issue a HTTP request and parse CLAM XML response, this is a low-level function called by all of the higher-level communicaton methods in this class, use those instead"""

        requestparams = self.initrequest(data)


        if method == 'POST':
            request = requests.post
        elif method == 'DELETE':
            request = requests.delete
        elif method == 'PUT':
            request = requests.put
        else:
            request = requests.get

        r = request(self.url + url,**requestparams)

        if r.status_code == 400:
            raise BadRequest()
        elif r.status_code == 401:
            raise AuthRequired()
        elif r.status_code == 403:
            content = r.text
            data = self._parse(content)
            if data:
                print(content,file=sys.stderr)
                raise PermissionDenied(data)
            else:
                raise PermissionDenied(content)
        elif r.status_code == 404 and data:
            raise NotFound(r.text)
        elif r.status_code == 500:
            raise ServerError(r.text)
        elif r.status_code == 405:
            raise ServerError("Server returned 405: Method not allowed for " + method + " on " + self.url + url)
        elif r.status_code == 408:
            raise TimeOut()
        elif not (r.status_code >= 200 and r.status_code <= 299):
            raise Exception("An error occured, return code " + str(r.status_code))

        return self._parse(r.text)


    def _parse(self, content):
        """Parses CLAM XML data and returns a ``CLAMData`` object. For internal use. Raises `ParameterError` exception on parameter errors."""
        if content.find('<clam') != -1:
            data = CLAMData(content,self)
            if data.errors:
                error = data.parametererror()
                if error:
                    raise ParameterError(error)
            return data
        else:
            return True

    def index(self):
        """Get index of projects. Returns a ``CLAMData`` instance. Use CLAMData.projects for the index of projects."""
        return self.request('')

    def get(self, project):
        """Query the project status. Returns a ``CLAMData`` instance or raises an exception according to the returned HTTP Status code"""
        try:
            data = self.request(project + '/')
        except:
            raise
        if not isinstance(data, CLAMData):
            raise Exception("Unable to retrieve CLAM Data")
        else:
            return data


    def create(self,project):
        """Create a new project::

           client.create("myprojectname")
        """
        return self.request(project + '/', 'PUT')



    def action(self, id, **kwargs):
        """Query an action, specify the parameters for the action as keyword parameters. An optional keyword parameter method='GET' (default) or method='POST' can be set."""
        if 'method' in kwargs:
            method = kwargs['method']
            del kwargs['method']
        else:
            method = 'GET'

        return self.request('/actions/' + id, method, kwargs)



    def start(self, project, **parameters):
        """Start a run. ``project`` is the ID of the project, and ``parameters`` are keyword arguments for
        the global parameters. Returns a ``CLAMData`` object or raises exceptions. Note that no exceptions are raised on parameter errors, you have to check for those manually! (Use startsafe instead if want Exceptions on parameter errors)::

            response = client.start("myprojectname", parameter1="blah", parameterX=4.2)

        """
        auth = None
        if 'auth' in parameters:
            auth = parameters['auth']
            del parameters['auth']
        for key in parameters:
            if isinstance(parameters[key],list) or isinstance(parameters[key],tuple):
                parameters[key] = ",".join(parameters[key])

        return self.request(project + '/', 'POST', parameters)

    def startsafe(self, project, **parameters):
        """Start a run. ``project`` is the ID of the project, and ``parameters`` are keyword arguments for
        the global parameters. Returns a ``CLAMData`` object or raises exceptions. This version, unlike ``start()``, raises Exceptions (``ParameterError``) on parameter errors.

            response = client.startsafe("myprojectname", parameter1="blah", parameterX=4.2)

        """

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
        """aborts AND deletes a project::

            client.delete("myprojectname")
        """
        return self.request(project + '/', 'DELETE')

    def abort(self, project): #alias
        """aborts AND deletes a project (alias of delete() )::

            client.abort("myprojectname")
        """
        return self.abort(project)


    def downloadarchive(self, project, targetfile, format = 'zip'):
        """Download all output files as a single archive:

        * *targetfile* - path for the new local file to be written
        * *format* - the format of the archive, can be 'zip','gz','bz2'

        Example::

            client.downloadarchive("myproject","allresults.zip","zip")

        """
        requestparams = self.initrequest()
        requestparams['data'] = {'format':format}
        r = requests.get(self.url + project + '/output/',**requestparams)
        CHUNK = 16 * 1024
        for chunk in r.iter_content(chunk_size=CHUNK):
            if chunk: # filter out keep-alive new chunks
                targetfile.write(chunk)
                targetfile.flush()

    def getinputfilename(self, inputtemplate, filename):
        """Determine the final filename for an input file given an inputtemplate and a given filename.

        Example::

            filenameonserver = client.getinputfilename("someinputtemplate","/path/to/local/file")

        """
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
        """Parse CLAM Upload XML Responses. For internal use"""
        if not isinstance(node,ElementTree._Element):
            try:
                node = ElementTree.parse(BytesIO(node.encode('utf-8'))).getroot()
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
        """Add/upload an input file to the CLAM service. Supports proper file upload streaming.

        project - the ID of the project you want to add the file to.
        inputtemplate - The input template you want to use to add this file (InputTemplate instance)
        sourcefile - The file you want to add: string containing a filename (or instance of ``file``)

        Keyword arguments (optional but recommended!):
            * ``filename`` - the filename on the server (will be same as sourcefile if not specified)
            * ``metadata`` - A metadata object.
            * ``metafile`` - A metadata file (filename)

        Any other keyword arguments will be passed as metadata and matched with the input template's parameters.

        Example::

            client.addinputfile("myproject", "someinputtemplate", "/path/to/local/file")

        With metadata, assuming such metadata parameters are defined::

            client.addinputfile("myproject", "someinputtemplate", "/path/to/local/file", parameter1="blah", parameterX=3.5)

        """
        if isinstance( inputtemplate, str) or (sys.version < '3' and isinstance( inputtemplate, unicode)): #pylint: disable=undefined-variable
            data = self.get(project) #causes an extra query to server
            inputtemplate = data.inputtemplate(inputtemplate)
        elif not isinstance(inputtemplate, InputTemplate):
            raise Exception("inputtemplate must be instance of InputTemplate. Get from CLAMData.inputtemplate(id)")

        if not isinstance(sourcefile, IOBase):
            sourcefile = open(sourcefile,'rb')
            if 'filename' in kwargs:
                filename = self.getinputfilename(inputtemplate, kwargs['filename'])
            else:
                filename = self.getinputfilename(inputtemplate, os.path.basename(sourcefile.name) )

        data = {"file": (filename,sourcefile,inputtemplate.formatclass.mimetype), 'inputtemplate': inputtemplate.id}
        for key, value in kwargs.items():
            if key == 'filename':
                pass #nothing to do
            elif key == 'metadata':
                assert isinstance(value, CLAMMetaData)
                data['metadata'] =  value.xml()
            elif key == 'metafile':
                data['metafile'] = open(value,'rb')
            else:
                data[key] = value


        requestparams = self.initrequest(data)
        if 'auth'in requestparams:
            #TODO: streaming support doesn't work with authentication unfortunately, disabling streaming for now:
            del data['file']
            requestparams['data'] = data
            requestparams['files'] = [('file', (filename,sourcefile, inputtemplate.formatclass.mimetype))]
            if 'metafile' in kwargs:
                del data['metafile']
                requestparams['files'].append(('metafile',('.'+ filename + '.METADATA', open(kwargs['metafile'],'rb'), 'text/xml')))
        else:
            #streaming support
            encodeddata = MultipartEncoder(fields=requestparams['data']) #from requests-toolbelt, necessary for streaming support
            requestparams['data'] = encodeddata
            requestparams['headers']['Content-Type'] = encodeddata.content_type
        r = requests.post(self.url + project + '/input/' + filename,**requestparams)
        sourcefile.close()

        if r.status_code == 400:
            raise BadRequest()
        elif r.status_code == 401:
            raise AuthRequired()
        elif r.status_code == 403:
            if r.text[0] == '<':
                #XML response
                return self._parseupload(r.text)
            else:
                raise PermissionDenied(r.text)
        elif r.status_code == 404:
            raise NotFound(r.text)
        elif r.status_code == 500:
            raise ServerError(r.text)
        elif r.status_code == 405:
            raise ServerError("Server returned 405: Method not allowed for POST on " + self.url + project + '/input/' + filename)
        elif r.status_code == 408:
            raise TimeOut()
        elif not (r.status_code >= 200 and r.status_code <= 299):
            raise Exception("An error occured, return code " + str(r.status_code))

        return self._parseupload(r.text)



    def addinput(self, project, inputtemplate, contents, **kwargs):
        """Add an input file to the CLAM service. Explictly providing the contents as a string. This is not suitable for large files as the contents are kept in memory! Use ``addinputfile()`` instead for large files.

        project - the ID of the project you want to add the file to.
        inputtemplate - The input template you want to use to add this file (InputTemplate instance)
        contents - The contents for the file to add (string)

        Keyword arguments:
            * filename - the filename on the server (mandatory!)
            * metadata - A metadata object.
            * metafile - A metadata file (filename)

        Any other keyword arguments will be passed as metadata and matched with the input template's parameters.

        Example::

            client.addinput("myproject", "someinputtemplate", "This is a test.", filename="test.txt")

        With metadata, assuming such metadata parameters are defined::

            client.addinput("myproject", "someinputtemplate", "This is a test.", filename="test.txt", parameter1="blah", parameterX=3.5))

        """
        if isinstance( inputtemplate, str) or (sys.version < '3' and isinstance( inputtemplate, unicode)): #pylint: disable=undefined-variable
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


        requestparams = self.initrequest(data)
        r = requests.post(self.url + project + '/input/' + filename,**requestparams)

        if r.status_code == 400:
            raise BadRequest()
        elif r.status_code == 401:
            raise AuthRequired()
        elif r.status_code == 403:
            if r.text[0] == '<':
                #XML response
                return self._parseupload(r.text)
            else:
                raise PermissionDenied(r.text)
        elif r.status_code == 404:
            raise NotFound(r.text)
        elif r.status_code == 500:
            raise ServerError(r.text)
        elif r.status_code == 405:
            raise ServerError("Server returned 405: Method not allowed for POST on " + self.url + project + '/input/' + filename)
        elif r.status_code == 408:
            raise TimeOut()
        elif not (r.status_code >= 200 and r.status_code <= 299):
            raise Exception("An error occured, return code " + str(r.status_code))

        return self._parseupload(r.text)



    def upload(self,project, inputtemplate, sourcefile, **kwargs):
        """Alias for ``addinputfile()``"""
        return self.addinputfile(project, inputtemplate,sourcefile, **kwargs)

    def download(self, project, filename, targetfilename, loadmetadata=False):
        """Download an output file"""
        f = CLAMOutputFile(self.url + project,  filename, loadmetadata, self)
        f.copy(targetfilename)

