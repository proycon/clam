#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Webservice --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#
#       Centre for Language and Speech Technology / Language Machines
#       Radboud University Nijmegen
#
#       Licensed under GPLv3
#
###############################################################

from __future__ import print_function, unicode_literals, division, absolute_import #for python 2

import flask
import werkzeug
import shutil
import os
import io
import stat
import subprocess
import glob
import sys
import datetime
import random
import re
import hashlib
import requests
import getopt
import time
import socket
import json
import mimetypes
from copy import copy #shallow copy (use deepcopy for deep)

if __name__ == "__main__":
    sys.path.append(sys.path[0] + '/..')
    #os.environ['PYTHONPATH'] = sys.path[0] + '/..'

import clam.common.status
import clam.common.parameters
import clam.common.formats
import clam.common.auth
import clam.common.oauth
import clam.common.data
from clam.common.util import globsymlinks, setdebug, setlog, setlogfile, printlog, printdebug, xmlescape, withheaders
import clam.config.defaults as settings #will be overridden by real settings later
settings.STANDALONEURLPREFIX = ''

try:
    from requests_oauthlib import OAuth2Session
except ImportError:
    print( "WARNING: No OAUTH2 support available in your version of Python! Install python-requests-oauthlib if you plan on using OAUTH2 for authentication!", file=sys.stderr)

try:
    import MySQLdb
except ImportError:
    print("WARNING: No MySQL support available in your version of Python! pip install mysqlclient if you plan on using MySQL for authentication",file=sys.stderr)

try:
    import foliatools
except ImportError:
    foliatools = None

try:
    import uwsgi
    UWSGI = True
except ImportError:
    UWSGI = False


VERSION = '0.99'

DEBUG = False

DATEMATCH = re.compile(r'^[\d\.\-\s:]*$')

settingsmodule = None #will be overwritten later

setlog(sys.stderr)

HOST = PORT = None


if sys.version < '3':
    class FileNotFoundError(IOError):
        pass

def error(msg):
    if __name__ == '__main__':
        print("ERROR: " + msg, file=sys.stderr)
        sys.exit(1)
    else:
        raise Exception(msg) #Raise python errors if we were not directly invoked

def warning(msg):
    print("WARNING: " + msg, file=sys.stderr)


def userdb_lookup_dict(user, **authsettings):
    printdebug("Looking up user " + user)
    return settings.USERS[user] #possible KeyError is captured later


def userdb_lookup_mysql(user, **authsettings):
    printdebug("Looking up user " + user + " in MySQL")
    host,port, mysqluser,passwd, database, table, userfield, passwordfield, accesslist, denylist = validate_users_mysql()
    if denylist and user in denylist:
        printdebug("User in denylist")
        raise KeyError
    if accesslist and not (user in accesslist):
        printdebug("User not in accesslist")
        raise KeyError
    if sys.version >= '3' and isinstance(passwd,bytes): passwd = str(passwd,'utf-8')
    db = MySQLdb.connect(host=host,user=mysqluser,passwd=passwd,db=database, charset='utf8', use_unicode=True)
    cursor = db.cursor()
    #simple protection against mysql injection
    user = user.replace("'","")
    user = user.replace(";","")
    sql = "SELECT `" + userfield + "`, `" + passwordfield + "` FROM `" + table + "` WHERE " + userfield + "='" + user + "' LIMIT 1"
    cursor.execute(sql)
    password = None
    while True:
        data = cursor.fetchone()
        if data:
            user, password = data
        else:
            break
    cursor.close()
    db.close()
    if password:
        printdebug("Password retrieved")
        return password
    else:
        printdebug("User not found")
        raise KeyError




def validate_users_mysql():
    if not settings.USERS_MYSQL:
        raise Exception("No USERS_MYSQL configured")
    if 'host' in settings.USERS_MYSQL:
        host = settings.USERS_MYSQL['host']
    else:
        host = 'localhost'
    if 'port' in settings.USERS_MYSQL:
        port = int(settings.USERS_MYSQL['port'])
    else:
        port = 3306
    if 'user' in settings.USERS_MYSQL:
        user = settings.USERS_MYSQL['user']
    else:
        raise Exception("No MySQL user defined in USERS_MYSQL")
    if 'password' in settings.USERS_MYSQL:
        password = settings.USERS_MYSQL['password']
    else:
        raise Exception("No MySQL password defined in USERS_MYSQL")
    if 'database' in settings.USERS_MYSQL:
        database = settings.USERS_MYSQL['database']
    else:
        raise Exception("No MySQL database defined in USERS_MYSQL")
    if 'table' in settings.USERS_MYSQL:
        table = settings.USERS_MYSQL['table']
    else:
        raise Exception("No MySQL table defined in USERS_MYSQL")
    if 'userfield' in settings.USERS_MYSQL:
        userfield = settings.USERS_MYSQL['userfield']
    else:
        userfield = "username"
    if 'passwordfield' in settings.USERS_MYSQL:
        passwordfield = settings.USERS_MYSQL['passwordfield']
    else:
        passwordfield = "password"
    if 'accesslist' in settings.USERS_MYSQL:
        accesslist = settings.USERS_MYSQL['accesslist']
    else:
        accesslist = []
    if 'denylist' in settings.USERS_MYSQL:
        denylist = settings.USERS_MYSQL['denylist']
    else:
        denylist = []
    return host,port, user,password, database, table, userfield, passwordfield,accesslist, denylist


class Login(object):
    @staticmethod
    def GET():
        global auth
        oauthsession = OAuth2Session(settings.OAUTH_CLIENT_ID)
        try:
            code = flask.request.values['code']
        except:
            return flask.make_response('No code passed',403)
        try:
            state = flask.request.values['state']
        except:
            return flask.make_response('No state passed',403)

        d = oauthsession.fetch_token(settings.OAUTH_TOKEN_URL, client_secret=settings.OAUTH_CLIENT_SECRET,authorization_response=getrooturl() + '/login?code='+ code + '&state' + state )
        if not 'access_token' in d:
            return flask.make_response('No access token received from authorization provider',403)

        return withheaders(flask.make_response(flask.render_template('login.xml',version=VERSION, system_id=settings.SYSTEM_ID, system_name=settings.SYSTEM_NAME, system_description=settings.SYSTEM_DESCRIPTION, url=getrooturl(), oauth_access_token=oauth_encrypt(d['access_token']))))

def oauth_encrypt(oauth_access_token):
    if not oauth_access_token:
        return "" #no oauth
    else:
        return clam.common.oauth.encrypt(settings.OAUTH_ENCRYPTIONSECRET, oauth_access_token, flask.request.headers.get('REMOTE_ADDR',''))

class Logout(object):

    @staticmethod
    def GET(credentials = None):
        user, oauth_access_token = parsecredentials(credentials)
        if not settings.OAUTH_REVOKE_URL:
            return flask.make_response("No revoke mechanism defined: we recommend to clear your browsing history and cache instead, especially if you are on a public computer",403)
        else:
            response = requests.get(settings.OAUTH_REVOKE_URL + '/', data={'token': oauth_access_token })

            if response.status_code >= 200 and response.status_code < 300:
                return "Logout successful, have a nice day"
            else:
                return flask.make_response("Logout failed at remote end: we recommend to clear your browsing history and cache instead, especially if you are on a public computer",403)

        return "Logout successful, have a nice day"



def parsecredentials(credentials):
    oauth_access_token = ""
    if settings.OAUTH and isinstance(credentials, tuple):
        oauth_access_token = credentials[1]
        user = credentials[0]
    elif credentials:
        user = credentials
    else:
        user = 'anonymous'

    if '/' in user or user == '.' or user == '..' or len(user) > 200:
        return flask.make_response("Username invalid",403)
    return user, oauth_access_token



################# Views ##########################

#Are tied into flask later because at this point we don't have an app instance yet

def index(credentials = None):
    """Get list of projects"""
    projects = []
    user, oauth_access_token = parsecredentials(credentials)
    for f in glob.glob(settings.ROOT + "projects/" + user + "/*"): #TODO LATER: Implement some kind of caching
        if os.path.isdir(f):
            d = datetime.datetime.fromtimestamp(os.stat(f)[8])
            project = os.path.basename(f)
            projects.append( ( project , d.strftime("%Y-%m-%d %H:%M:%S") ) )

    errors = "no"
    errormsg = ""

    corpora = CLAMService.corpusindex()

    return withheaders(flask.make_response(flask.render_template('response.xml',
            version=VERSION,
            system_id=settings.SYSTEM_ID,
            system_name=settings.SYSTEM_NAME,
            system_description=settings.SYSTEM_DESCRIPTION,
            user=user,
            project=None,
            url=getrooturl(),
            statuscode=-1,
            statusmessage="",
            statuslog=[],
            completion=0,
            errors=errors,
            errormsg=errormsg,
            parameterdata=settings.PARAMETERS,
            inputsources=corpora,
            outputpaths=None,
            inputpaths=None,
            profiles=settings.PROFILES,
            datafile=None,
            projects=projects,
            actions=settings.ACTIONS,
            disableinterface=not settings.ENABLEWEBAPP,
            info=False,
            accesstoken=None,
            interfaceoptions=settings.INTERFACEOPTIONS,
            customhtml=settings.CUSTOMHTML_INDEX,
            oauth_access_token=oauth_encrypt(oauth_access_token)
    )))



def info(credentials=None):
    """Get info"""
    projects = []
    user, oauth_access_token = parsecredentials(credentials)
    for f in glob.glob(settings.ROOT + "projects/" + user + "/*"): #TODO LATER: Implement some kind of caching
        if os.path.isdir(f):
            d = datetime.datetime.fromtimestamp(os.stat(f)[8])
            project = os.path.basename(f)
            projects.append( ( project , d.strftime("%Y-%m-%d %H:%M:%S") ) )

    errors = "no"
    errormsg = ""

    corpora = CLAMService.corpusindex()

    return withheaders(flask.make_response(flask.render_template('response.xml',
            version=VERSION,
            system_id=settings.SYSTEM_ID,
            system_name=settings.SYSTEM_NAME,
            system_description=settings.SYSTEM_DESCRIPTION,
            user=user,
            project=None,
            url=getrooturl(),
            statuscode=-1,
            statusmessage="",
            statuslog=[],
            completion=0,
            errors=errors,
            errormsg=errormsg,
            parameterdata=settings.PARAMETERS,
            inputsources=corpora,
            outputpaths=None,
            inputpaths=None,
            profiles=settings.PROFILES,
            datafile=None,
            projects=projects,
            actions=settings.ACTIONS,
            info=True,
            disableinterface=not settings.ENABLEWEBAPP,
            accesstoken=None,
            interfaceoptions=settings.INTERFACEOPTIONS,
            customhtml=settings.CUSTOMHTML_INDEX,
            oauth_access_token=oauth_encrypt(oauth_access_token)
    )))

class Admin:
    @staticmethod
    def index(credentials=None):
        """Get list of projects"""
        user, oauth_access_token = parsecredentials(credentials)
        if not settings.ADMINS or not user in settings.ADMINS:
            return flask.make_response('You shall not pass!!! You are not an administrator!',403)

        usersprojects = {}
        for f in glob.glob(settings.ROOT + "projects/*"):
            if os.path.isdir(f):
                u = os.path.basename(f)
                usersprojects[u] = []

                for f2 in glob.glob(settings.ROOT + "projects/" + u + "/*"):
                    if os.path.isdir(f2):
                        d = datetime.datetime.fromtimestamp(os.stat(f2)[8])
                        p = os.path.basename(f2)
                        usersprojects[u].append( (p, d.strftime("%Y-%m-%d %H:%M:%S"), Project.status(p,u)[0]  ) )

        for u in usersprojects:
            usersprojects[u] = sorted(usersprojects[u])

        return withheaders(flask.make_response(flask.render_template('admin.html',
                version=VERSION,
                system_id=settings.SYSTEM_ID,
                system_name=settings.SYSTEM_NAME,
                system_description=settings.SYSTEM_DESCRIPTION,
                user=user,
                url=getrooturl(),
                usersprojects = sorted(usersprojects.items()),
                oauth_access_token=oauth_encrypt(oauth_access_token)
        )), "text/html; charset=UTF-8" )

    @staticmethod
    def handler(command, targetuser, project, credentials=None):
        user, oauth_access_token = parsecredentials(credentials)
        if not settings.ADMINS or not user in settings.ADMINS:
            return flask.make_response('You shall not pass!!! You are not an administrator!',403)

        if command == 'inspect':
            inputfiles = []
            for f in glob.glob(settings.ROOT + "projects/" + targetuser + "/" + project + "/input/*"):
                f = os.path.basename(f)
                if f[0] != '.':
                    inputfiles.append(f)
            outputfiles = []
            for f in glob.glob(settings.ROOT + "projects/" + targetuser + "/" + project + "/output/*"):
                f = os.path.basename(f)
                if f[0] != '.':
                    outputfiles.append(f)
            return withheaders(flask.make_response(flask.render_template('admininspect.html',
                    version=VERSION,
                    system_id=settings.SYSTEM_ID,
                    system_name=settings.SYSTEM_NAME,
                    system_description=settings.SYSTEM_DESCRIPTION,
                    user=targetuser,
                    project=project,
                    inputfiles=sorted(inputfiles),
                    outputfiles=sorted(outputfiles),
                    url=getrooturl(),
                    oauth_access_token=oauth_encrypt(oauth_access_token)
            )), "text/html; charset=UTF-8" )
        elif command == 'abort':
            p = Project()
            if p.abort(project, targetuser):
                return "Ok"
            else:
                return flask.make_response('Failed',403)
        elif command == 'delete':
            d = Project.path(project, targetuser)
            if os.path.isdir(d):
                shutil.rmtree(d)
                return "Ok"
            else:
                return flask.make_response('Not Found',403)
        else:
            return flask.make_response('No such command: ' + command,403)

    @staticmethod
    def downloader(targetuser, project, type, filename, credentials=None):
        user, oauth_access_token = parsecredentials(credentials)
        if not settings.ADMINS or not user in settings.ADMINS:
            return flask.make_response('You shall not pass!!! You are not an administrator!',403)

        if type == 'input':
            try:
                outputfile = clam.common.data.CLAMInputFile(Project.path(project, targetuser), filename)
            except:
                raise flask.abort(404)
        elif type == 'output':
            try:
                outputfile = clam.common.data.CLAMOutputFile(Project.path(project, targetuser), filename)
            except:
                raise flask.abort(404)
        else:
            return flask.make_response('Invalid type',403)

        if outputfile.metadata:
            headers = outputfile.metadata.httpheaders()
            mimetype = outputfile.metadata.mimetype
        else:
            headers = {}
            mimetype = 'application/octet-stream'
        try:
            return withheaders(flask.Response( (line for line in outputfile) ), mimetype, headers )
        except UnicodeError:
            return flask.make_response("Output file " + str(outputfile) + " is not in the expected encoding! Make sure encodings for output templates service configuration file are accurate.",500)
        except FileNotFoundError:
            raise flask.abort(404)
        except IOError:
            raise flask.abort(404)





def getrooturl(): #not a view
    if settings.FORCEURL:
        return settings.FORCEURL
    else:
        if settings.PORT == 443:
            url = 'https://' + settings.HOST
        else:
            url = 'http://' + settings.HOST
        if settings.PORT != 80 and settings.PORT != 443:
            url += ':' + str(settings.PORT)
        if settings.URLPREFIX and settings.URLPREFIX != '/':
            if settings.URLPREFIX[0] != '/':
                url += '/'
            url += settings.URLPREFIX
        if url[-1] == '/': url = url[:-1]
        return url

def getbinarydata(path, buffersize=16*1024):
    with io.open(path,'rb') as f:
        while True:
            data = f.read(buffersize)
            if not data:
                break
            else:
                yield data
class Project:
    """This class simply groups project methods, is not instantiated and does not offer any kind of persistence, all methods are static"""

    @staticmethod
    def validate(project):
        return re.match(r'^\w+$',project, re.UNICODE)

    @staticmethod
    def path(project, credentials):
        """Get the path to the project (static method)"""
        user, oauth_access_token = parsecredentials(credentials)
        return settings.ROOT + "projects/" + user + '/' + project + "/"

    @staticmethod
    def create(project, credentials):
        """Create project skeleton if it does not already exist (static method)"""

        if not settings.COMMAND:
            return flask.make_response("Projects disabled, no command configured",404)

        user, oauth_access_token = parsecredentials(credentials)
        if not Project.validate(project):
            return flask.make_response('Invalid project ID',403)
        printdebug("Checking if " + settings.ROOT + "projects/" + user + '/' + project + " exists")
        if not project:
            return flask.make_response('No project name',403)
        if not os.path.isdir(settings.ROOT + "projects/" + user):
            printlog("Creating user directory '" + user + "'")
            os.makedirs(settings.ROOT + "projects/" + user)
            if not os.path.isdir(settings.ROOT + "projects/" + user): #verify:
                return flask.make_response("Directory " + settings.ROOT + "projects/" + user + " could not be created succesfully",403)
        if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project):
            printlog("Creating project '" + project + "'")
            os.makedirs(settings.ROOT + "projects/" + user + '/' + project)
        if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/input/'):
            os.makedirs(settings.ROOT + "projects/" + user + '/' + project + "/input")
            if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/input'):
                return flask.make_response("Input directory " + settings.ROOT + "projects/" + user + '/' + project + "/input/  could not be created succesfully",403)
        if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/output/'):
            os.makedirs(settings.ROOT + "projects/" + user + '/' + project + "/output")
            if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/output'):
                return flask.make_response("Output directory " + settings.ROOT + "projects/" + user + '/' + project + "/output/  could not be created succesfully",403)
            #if not settings.PROJECTS_PUBLIC:
            #    f = codecs.open(settings.ROOT + "projects/" + user + '/' + project + '/.users','w','utf-8')
            #    f.write(user + "\n")
            #    f.close()


    @staticmethod
    def pid(project, user):
        pidfile = Project.path(project, user) + '.pid'
        if os.path.isfile(pidfile):
            f = open(pidfile,'r')
            pid = int(f.read(os.path.getsize(pidfile)))
            f.close()
            return pid
        else:
            return 0

    @staticmethod
    def running(project, user):
        pidfile = Project.path(project, user) + '.pid'
        if os.path.isfile(pidfile) and not os.path.isfile(Project.path(project, user) + ".done"):
            f = open(pidfile,'r')
            pid = int(f.read(os.path.getsize(pidfile)))
            f.close()
            try:
                os.kill(pid, 0) #raises error if pid doesn't exist
                return True
            except:
                f = open(Project.path(project, user) + ".done", 'w')
                f.write(str(1) )
                f.close()
                os.unlink(pidfile)
                return False
        else:
            return False


    @staticmethod
    def abort(project, user):
        if Project.pid(project, user) == 0:
            return False
        printlog("Aborting process of project '" + project + "'" )
        f = open(Project.path(project,user) + ".abort", 'w')
        f.close()
        os.chmod( Project.path(project,user) + ".abort", 0o777)
        while not os.path.exists(Project.path(project, user) + ".done"):
            printdebug("Waiting for process to die")
            time.sleep(1)
        return True

    @staticmethod
    def done(project,user):
        return os.path.isfile(Project.path(project, user) + ".done")

    @staticmethod
    def aborted(project,user):
        return os.path.isfile(Project.path(project, user) + ".aborted")


    @staticmethod
    def exitstatus(project, user):
        f = open(Project.path(project, user) + ".done")
        status = int(f.read(1024))
        f.close()
        return status

    @staticmethod
    def exists(project, credentials):
        """Check if the project exists"""
        user, oauth_access_token = parsecredentials(credentials)
        printdebug("Checking if project " + project + " exists for " + user)
        return os.path.isdir(Project.path(project, user))

    @staticmethod
    def statuslog(project, user):
        statuslog = []
        statusfile = Project.path(project,user) + ".status"
        totalcompletion = 0
        if os.path.isfile(statusfile):
            prevmsg = None
            f = open(statusfile)
            for line in f:
                line = line.strip()
                if line:
                    message = ""
                    completion = 0
                    timestamp = ""
                    for field in line.split("\t"):
                        if field:
                            if field[-1] == '%' and field[:-1].isdigit():
                                completion = int(field[:-1])
                                if completion > 0:
                                    totalcompletion = completion
                            elif DATEMATCH.match(field):
                                if field.isdigit():
                                        try:
                                            d = datetime.datetime.fromtimestamp(float(field))
                                            timestamp = d.strftime("%d/%b/%Y %H:%M:%S")
                                        except:
                                            pass
                            else:
                                message += " " + field

                    if message and (message != prevmsg):
                        #print "STATUSLOG: t=",timestamp,"c=",completion,"msg=" + message.strip()
                        statuslog.append( (message.strip(), timestamp, completion) )
                        prevmsg = message
            msg = f.read(os.path.getsize(statusfile))
            f.close()
            statuslog.reverse()
        return statuslog, totalcompletion

    @staticmethod
    def status(project, user):
        global DATEMATCH
        if Project.running(project, user):
            statuslog, completion = Project.statuslog(project, user)
            if statuslog:
                return (clam.common.status.RUNNING, statuslog[0][0],statuslog, completion)
            else:
                return (clam.common.status.RUNNING, "The system is running",  [], 0) #running
        elif Project.done(project, user):
            statuslog, completion = Project.statuslog(project, user)
            if Project.aborted(project,user):
                if not statuslog:
                    completion = 100
                return (clam.common.status.DONE, "Aborted! Output may be partial or unavailable", statuslog, completion)
            else:
                if statuslog:
                    return (clam.common.status.DONE, statuslog[0][0],statuslog, completion)
                else:
                    return (clam.common.status.DONE, "Done", statuslog, 100)
        else:
            return (clam.common.status.READY, "Accepting new input files and selection of parameters", [], 0)

    @staticmethod
    def status_json(project, credentials=None):
        postdata = flask.request.values
        if 'user' in postdata:
            user = flask.request.values['user']
        else:
            user = 'anonymous'
        if 'accesstoken' in postdata:
            accesstoken = flask.request.values['accesstoken']
        else:
            return "{success: false, error: 'No accesstoken given'}"
        if accesstoken != Project.getaccesstoken(user,project):
            return "{success: false, error: 'Invalid accesstoken given'}"
        if not os.path.exists(Project.path(project, user)):
            return "{success: false, error: 'Destination does not exist'}"

        statuscode, statusmsg, statuslog, completion = Project.status(project,user)
        return json.dumps({'success':True, 'statuscode':statuscode,'statusmsg':statusmsg, 'statuslog': statuslog, 'completion': completion})

    @staticmethod
    def inputindex(project, user, d = ''):
        prefix = Project.path(project, user) + 'input/'
        for f in glob.glob(prefix + d + "/*"):
            if os.path.basename(f)[0] != '.': #always skip all hidden files
                if os.path.isdir(f):
                    for result in Project.inputindex(project, user, f[len(prefix):]):
                        yield result
                else:
                    file = clam.common.data.CLAMInputFile(Project.path(project,user), f[len(prefix):])
                    file.attachviewers(settings.PROFILES) #attaches converters as well
                    yield file


    @staticmethod
    def outputindex(project, user, d = ''):
        prefix = Project.path(project, user) + 'output/'
        for f in glob.glob(prefix + d + "/*"):
            if os.path.basename(f)[0] != '.': #always skip all hidden files
                if os.path.isdir(f):
                    for result in Project.outputindex(project, user, f[len(prefix):]):
                        yield result
                else:
                    file = clam.common.data.CLAMOutputFile(Project.path(project,user), f[len(prefix):])
                    file.attachviewers(settings.PROFILES) #attaches converters as well
                    yield file

    @staticmethod
    def inputindexbytemplate(project, user, inputtemplate):
        """Retrieve sorted index for the specified input template"""
        index = []
        prefix = Project.path(project, user) + 'input/'
        for linkf, f in globsymlinks(prefix + '.*.INPUTTEMPLATE.' + inputtemplate.id + '.*'):
            seq = int(linkf.split('.')[-1])
            index.append( (seq,f) )

        #yield CLAMFile objects in proper sequence
        for seq, f in sorted(index):
            yield seq, clam.common.data.CLAMInputFile(Project.path(project, user), f[len(prefix):])


    @staticmethod
    def outputindexbytemplate(project, user, outputtemplate):
        """Retrieve sorted index for the specified input template"""
        index = []
        prefix = Project.path(project, user) + 'output/'
        for linkf, f in globsymlinks(prefix + '.*.OUTPUTTEMPLATE.' + outputtemplate.id + '.*'):
            seq = int(linkf.split('.')[-1])
            index.append( (seq,f) )

        #yield CLAMFile objects in proper sequence
        for seq, f in sorted(index):
            yield seq, clam.common.data.CLAMOutputFile(Project.path(project, user), f[len(prefix):])



    #main view
    @staticmethod
    def response(user, project, parameters, errormsg = "", datafile = False, oauth_access_token=""):
        global VERSION

        #check if there are invalid parameters:
        if not errormsg:
            errors = "no"
        else:
            errors = "yes"

        statuscode, statusmsg, statuslog, completion = Project.status(project, user)

        customhtml = ""
        if statuscode == clam.common.status.READY:
            customhtml = settings.CUSTOMHTML_PROJECTSTART

        inputpaths = []
        if statuscode == clam.common.status.READY or statuscode == clam.common.status.DONE:
            inputpaths = Project.inputindex(project, user)



        if statuscode == clam.common.status.DONE:
            outputpaths = Project.outputindex(project, user)
            if Project.exitstatus(project, user) != 0: #non-zero codes indicate errors!
                errors = "yes"
                errormsg = "An error occurred within the system. Please inspect the error log for details"
                printlog("Child process failed, exited with non zero-exit code.")
            customhtml = settings.CUSTOMHTML_PROJECTDONE
        else:
            outputpaths = []


        for parametergroup, parameterlist in parameters:
            for parameter in parameterlist:
                if parameter.error:
                    errors = "yes"
                    if not errormsg: errormsg = "One or more parameters are invalid"
                    printlog("One or more parameters are invalid: " + parameter.id)
                    break

        return withheaders(flask.make_response(flask.render_template('response.xml',
                version=VERSION,
                system_id=settings.SYSTEM_ID,
                system_name=settings.SYSTEM_NAME,
                system_description=settings.SYSTEM_DESCRIPTION,
                user=user,
                project=project,
                url=getrooturl(),
                statuscode=statuscode,
                statusmessage=statusmsg,
                statuslog=statuslog,
                completion=completion,
                errors=errors,
                errormsg=errormsg,
                parameterdata=parameters,
                inputsources=settings.INPUTSOURCES,
                outputpaths=outputpaths,
                inputpaths=inputpaths,
                profiles=settings.PROFILES,
                datafile=datafile,
                projects=[],
                actions=settings.ACTIONS,
                disableinterface=not settings.ENABLEWEBAPP,
                info=False,
                accesstoken=Project.getaccesstoken(user,project),
                interfaceoptions=settings.INTERFACEOPTIONS,
                customhtml=customhtml,
                oauth_access_token=oauth_encrypt(oauth_access_token)
        )))


    @staticmethod
    def getaccesstoken(user,project):
        #for fineuploader, not oauth
        h = hashlib.md5()
        clear = user+ ':' + settings.PRIVATEACCESSTOKEN + ':' + project
        if sys.version < '3' and isinstance(clear,unicode): #pylint: disable=undefined-variable
            h.update(clear.encode('utf-8'))
        if sys.version >= '3' and isinstance(clear,str):
            h.update(clear.encode('utf-8'))
        else:
            h.update(clear)
        return h.hexdigest()

    #exposed views:

    @staticmethod
    def get(project, credentials=None):
        """Main Get method: Get project state, parameters, outputindex"""
        user, oauth_access_token = parsecredentials(credentials)
        if not Project.exists(project, user):
            return flask.make_response("Project " + project + " was not found for user " + user,404) #404
        else:
            #if user and not Project.access(project, user) and not user in settings.ADMINS:
            #    return flask.make_response("Access denied to project " +  project + " for user " + user, 401) #401
            return Project.response(user, project, settings.PARAMETERS,"",False,oauth_access_token) #200


    @staticmethod
    def new(project, credentials=None):
        """Create an empty project"""
        user, oauth_access_token = parsecredentials(credentials)
        Project.create(project, user)
        msg = "Project " + project + " has been created for user " + user
        if oauth_access_token:
            extraloc = '?oauth_access_token=' + oauth_access_token
        else:
            extraloc = ''
        return flask.make_response(msg, 201, {'Location': getrooturl() + '/' + project + '/' + extraloc, 'Content-Type':'text/plain','Content-Length': len(msg),'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE', 'Access-Control-Allow-Headers': 'Authorization'}) #HTTP CREATED

    @staticmethod
    def start(project, credentials=None):
        """Start execution"""
        global settingsmodule
        user, oauth_access_token = parsecredentials(credentials)
        Project.create(project, user)
        #if user and not Project.access(project, user):
        #    return flask.make_response("Access denied to project " + project +  " for user " + user,401) #401

        statuscode, _, _, _  = Project.status(project, user)
        if statuscode != clam.common.status.READY:
            if oauth_access_token:
                return flask.redirect(getrooturl() + '/' + project + '/?oauth_access_token=' + oauth_access_token)
            else:
                return flask.redirect(getrooturl() + '/' + project)

        #Generate arguments based on POSTed parameters
        commandlineparams = []
        postdata = flask.request.values

        errors, parameters, commandlineparams = clam.common.data.processparameters(postdata, settings.PARAMETERS)

        sufresources, resmsg = sufficientresources()
        if not sufresources:
            printlog("*** NOT ENOUGH SYSTEM RESOURCES AVAILABLE: " + resmsg + " ***")
            return flask.make_response("There are not enough system resources available to accommodate your request. " + resmsg + " .Please try again later.",503)
        if not errors: #We don't even bother running the profiler if there are errors
            matchedprofiles = clam.common.data.profiler(settings.PROFILES, Project.path(project, user), parameters, settings.SYSTEM_ID, settings.SYSTEM_NAME, getrooturl(), printdebug)

        if errors:
            #There are parameter errors, return 403 response with errors marked
            printlog("There are parameter errors, not starting.")
            return flask.make_response(Project.response(user, project, parameters,"",False,oauth_access_token),403, {'Content-Type':'application/xml'} )
        elif not matchedprofiles:
            printlog("No profiles matching, not starting.")
            return flask.make_response(Project.response(user, project, parameters, "No profiles matching input and parameters, unable to start. Are you sure you added all necessary input files and set all necessary parameters?", False, oauth_access_token),403, {'Content-Type':'application/xml'} )
        else:
            #write clam.xml output file
            f = io.open(Project.path(project, user) + "clam.xml",'wb')
            f.write(Project.response(user, project, parameters, "",True, oauth_access_token).data)
            f.close()



            #Start project with specified parameters
            cmd = settings.COMMAND
            cmd = cmd.replace('$PARAMETERS', " ".join(commandlineparams)) #commandlineparams is shell-safe
            #if 'usecorpus' in postdata and postdata['usecorpus']:
            #    corpus = postdata['usecorpus'].replace('..','') #security
            #    #use a preinstalled corpus:
            #    if os.path.exists(settings.ROOT + "corpora/" + corpus):
            #        cmd = cmd.replace('$INPUTDIRECTORY', settings.ROOT + "corpora/" + corpus + "/")
            #    else:
            #        raise web.webapi.NotFound("Corpus " + corpus + " not found")
            #else:
            cmd = cmd.replace('$INPUTDIRECTORY', Project.path(project, user) + 'input/')
            cmd = cmd.replace('$OUTPUTDIRECTORY',Project.path(project, user) + 'output/')
            cmd = cmd.replace('$STATUSFILE',Project.path(project, user) + '.status')
            cmd = cmd.replace('$DATAFILE',Project.path(project, user) + 'clam.xml')
            cmd = cmd.replace('$USERNAME',user if user else "anonymous")
            cmd = cmd.replace('$PROJECT',project) #alphanumberic only, shell-safe
            cmd = cmd.replace('$OAUTH_ACCESS_TOKEN',oauth_access_token)
            #everything should be shell-safe now
            if settings.COMMAND.find("2>") == -1:
                cmd += " 2> " + Project.path(project, user) + "output/error.log" #add error output

            pythonpath = ''
            try:
                pythonpath = ':'.join(settings.DISPATCHER_PYTHONPATH)
            except:
                pass
            if pythonpath:
                pythonpath = os.path.dirname(settings.__file__) + ':' + pythonpath
            else:
                pythonpath = os.path.dirname(settings.__file__)

            #if settings.DISPATCHER == 'clamdispatcher' and os.path.exists(settings.CLAMDIR + '/' + settings.DISPATCHER + '.py') and stat.S_IXUSR & os.stat(settings.CLAMDIR + '/' + settings.DISPATCHER+'.py')[stat.ST_MODE]:
            #    #backward compatibility for old configurations without setuptools
            #    cmd = settings.CLAMDIR + '/' + settings.DISPATCHER + '.py'
            #else:
            cmd = settings.DISPATCHER + ' ' + pythonpath + ' ' + settingsmodule + ' ' + Project.path(project, user) + ' ' + cmd
            if settings.REMOTEHOST:
                if settings.REMOTEUSER:
                    cmd = "ssh -o NumberOfPasswordPrompts=0 " + settings.REMOTEUSER + "@" + settings.REMOTEHOST + " " + cmd
                else:
                    cmd = "ssh -o NumberOfPasswordPrompts=0 " + settings.REMOTEHOST + " " + cmd
            printlog("Starting dispatcher " +  settings.DISPATCHER + " with " + settings.COMMAND + ": " + repr(cmd) + " ..." )
            #process = subprocess.Popen(cmd,cwd=Project.path(project), shell=True)
            process = subprocess.Popen(cmd,cwd=settings.CLAMDIR, shell=True)
            if process:
                pid = process.pid
                printlog("Started dispatcher with pid " + str(pid) )
                f = open(Project.path(project, user) + '.pid','w') #will be handled by dispatcher!
                f.write(str(pid))
                f.close()
                return flask.make_response(Project.response(user, project, parameters,"",False,oauth_access_token),202) #returns 202 - Accepted
            else:
                return flask.make_response("Unable to launch process",500)

    @staticmethod
    def delete(project, credentials=None):
        data = flask.request.values
        if 'abortonly' in data:
            abortonly = bool(data['abortonly'])
        else:
            abortonly = False
        user, oauth_access_token = parsecredentials(credentials)
        if not Project.exists(project, user):
            return flask.make_response("No such project: " + project + " for user " + user,404)
        statuscode, _, _, _  = Project.status(project, user)
        msg = ""
        if statuscode == clam.common.status.RUNNING:
            Project.abort(project, user)
            msg = "Aborted"
        if not abortonly:
            printlog("Deleting project '" + project + "'" )
            shutil.rmtree(Project.path(project, user))
            msg += " Deleted"
        msg = msg.strip()
        return withheaders(flask.make_response(msg),'text/plain',{'Content-Length':len(msg)})  #200


    @staticmethod
    def download_zip(project, credentials=None):
        user, _ = parsecredentials(credentials)
        return Project.getarchive(project, user,'zip')

    @staticmethod
    def download_targz(project, credentials=None):
        user, _ = parsecredentials(credentials)
        return Project.getarchive(project, user,'tar.gz')

    @staticmethod
    def download_tarbz2(project, credentials=None):
        user, _ = parsecredentials(credentials)
        return Project.getarchive(project, user,'tar.bz2')

    @staticmethod
    def getoutputfile(project, filename, credentials=None):
        user, oauth_access_token = parsecredentials(credentials)
        raw = filename.split('/')

        viewer = None
        requestid = None
        requestarchive = False

        if filename.strip('/') == "":
            #this is a request for everything
            requestarchive = True
            return Project.getarchive(project,user)
        elif filename in ("folia.xsl","folia2html.xsl"):
            return foliaxsl()
        elif len(raw) >= 2:
            #This MAY be a viewer/metadata request, check:
            if os.path.isfile(Project.path(project, user) + 'output/' +  "/".join(raw[:-1])):
                filename = "/".join(raw[:-1])
                requestid = raw[-1].lower()

        if not requestarchive:
            outputfile = clam.common.data.CLAMOutputFile(Project.path(project, user), filename)

        if requestid:
            if requestid == 'metadata':
                if outputfile.metadata:
                    return withheaders(flask.make_response(outputfile.metadata.xml()))
                else:
                    return flask.make_response("No metadata found!",404)
            else:
                #attach viewer data (also attaches converters!
                outputfile.attachviewers(settings.PROFILES)

                viewer = None
                for v in outputfile.viewers:
                    if v.id == requestid:
                        viewer = v
                if viewer:
                    output = viewer.view(outputfile, **flask.request.values)
                    if isinstance(output, flask.Response):
                        return output
                    else:
                        return withheaders(flask.Response(  (line for line in output ) , 200), viewer.mimetype) #streaming output
                else:
                    #Check for converters
                    for c in outputfile.converters:
                        if c.id == requestid:
                            converter = c
                    if converter:
                        return flask.Response( ( line for line in converter.convertforoutput(outputfile) ) )
                    else:
                        return flask.make_response("No such viewer or converter:" + requestid,404)
        elif not requestarchive:
            #normal request - return file contents

            #pro-actively check if file exists
            if not os.path.exists(str(outputfile)):
                raise flask.abort(404)

            if outputfile.metadata:
                headers = outputfile.metadata.httpheaders()
                mimetype = outputfile.metadata.mimetype
                printdebug("No metadata found for output file " + str(outputfile))
            else:
                headers = {}
                if os.path.basename(str(outputfile)) in ('log','error.log'):
                    mimetype = 'text/plain'
                else:
                    #guess mimetype
                    mimetype = mimetypes.guess_type(str(outputfile))[0]
                if not mimetype: mimetype = 'application/octet-stream'
            printdebug("Returning output file " + str(outputfile) + " with mimetype " + mimetype)
            try:
                return withheaders(flask.Response( (line for line in outputfile) ), mimetype, headers )
            except UnicodeError:
                return flask.make_response("Output file " + str(outputfile) + " is not in the expected encoding! Make sure encodings for output templates service configuration file are accurate.",500)
            except FileNotFoundError:
                raise flask.abort(404)
            except IOError:
                raise flask.abort(404)

    @staticmethod
    def deletealloutput(project, credentials=None):
        return Project.deleteoutputfile(project,None,credentials)

    @staticmethod
    def deleteoutputfile(project, filename, credentials=None):
        """Delete an output file"""

        user, oauth_access_token = parsecredentials(credentials)
        if filename: filename = filename.replace("..","") #Simple security

        if not filename or len(filename) == 0:
            #Deleting all output files and resetting
            Project.reset(project, user)
            msg = "Deleted"
            return withheaders(flask.make_response(msg), 'text/plain',{'Content-Length':len(msg)}) #200
        elif os.path.isdir(Project.path(project, user) + filename):
            #Deleting specified directory
            shutil.rmtree(Project.path(project, user) + filename)
            msg = "Deleted"
            return withheaders(flask.make_response(msg), 'text/plain',{'Content-Length':len(msg)}) #200
        else:
            try:
                file = clam.common.data.CLAMOutputFile(Project.path(project, user), filename)
            except:
                raise flask.abort(404)

            success = file.delete()
            if not success:
                raise flask.abort(404)
            else:
                msg = "Deleted"
                return withheaders(flask.make_response(msg), 'text/plain',{'Content-Length':len(msg)}) #200


    @staticmethod
    def reset(project, user):
        """Reset system, delete all output files and prepare for a new run"""
        d = Project.path(project, user) + "output"
        if os.path.isdir(d):
            shutil.rmtree(d)
            os.makedirs(d)
        else:
            raise flask.abort(404)
        if os.path.exists(Project.path(project, user) + ".done"):
            os.unlink(Project.path(project, user) + ".done")
        if os.path.exists(Project.path(project, user) + ".status"):
            os.unlink(Project.path(project, user) + ".status")

    @staticmethod
    def getarchive(project, user, format=None):
        """Generates and returns a download package (or 403 if one is already in the process of being prepared)"""
        if os.path.isfile(Project.path(project, user) + '.download'):
            #make sure we don't start two compression processes at the same time
            return flask.make_response('Another compression is already running',403)
        else:
            if not format:
                data = flask.request.values
                if 'format' in data:
                    format = data['format']
                else:
                    format = 'zip' #default

            #validation, security
            contentencoding = None
            if format == 'zip':
                contenttype = 'application/zip'
                command = "/usr/bin/zip -r" #TODO: do not hard-code path!
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".tar.gz"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".tar.gz")
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".tar.bz2"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".tar.bz2")
            elif format == 'tar.gz':
                contenttype = 'application/x-tar'
                contentencoding = 'gzip'
                command = "/bin/tar -czf"
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".zip"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".zip")
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".tar.bz2"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".tar.bz2")
            elif format == 'tar.bz2':
                contenttype = 'application/x-bzip2'
                command = "/bin/tar -cjf"
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".tar.gz"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".tar.gz")
                if os.path.isfile(Project.path(project, user) + "output/" + project + ".zip"):
                    os.unlink(Project.path(project, user) + "output/" + project + ".zip")
            else:
                return flask.make_response('Invalid archive format',403) #TODO: message won't show

            path = Project.path(project, user) + "output/" + project + "." + format

            if not os.path.isfile(path):
                printlog("Building download archive in " + format + " format")
                cmd = command + ' ' + project + '.' + format + ' *'
                printdebug(cmd)
                printdebug(Project.path(project, user)+'output/')
                process = subprocess.Popen(cmd, cwd=Project.path(project, user)+'output/', shell=True)
                if not process:
                    flask.make_response("Unable to make download package",500)
                else:
                    pid = process.pid
                    f = open(Project.path(project, user) + '.download','w')
                    f.write(str(pid))
                    f.close()
                    os.waitpid(pid, 0) #wait for process to finish
                    os.unlink(Project.path(project, user) + '.download')

            extraheaders = {}
            if contentencoding:
                extraheaders['Content-Encoding'] = contentencoding

            return withheaders(flask.Response( getbinarydata(path) ), contenttype, extraheaders )


    @staticmethod
    def getinputfile(project, filename, credentials=None):

        viewer = None
        requestid = None
        user, oauth_access_token = parsecredentials(credentials)

        raw = filename.split('/')

        if filename.strip('/') == "":
            #this is a request for the index
            return flask.make_response("Permission denied",403)
        elif filename in ("folia.xsl","folia2html.xsl"):
            return foliaxsl()
        elif len(raw) >= 2:
            #This MAY be a viewer/metadata request, check:
            if os.path.isfile(Project.path(project, user) + 'input/' +  "/".join(raw[:-1])):
                filename = "/".join(raw[:-1])
                requestid = raw[-1].lower()

        try:
            inputfile = clam.common.data.CLAMInputFile(Project.path(project, user), filename)
        except:
            raise flask.abort(404)

        if requestid:
            if requestid == 'metadata':
                if inputfile.metadata:
                    return withheaders(flask.make_response(inputfile.metadata.xml()))
                else:
                    return flask.make_response("No metadata found!",404)
            else:
                raise flask.abort(404)
        else:
            #normal request - return file contents

            #pro-actively check if file exists
            if not os.path.exists(str(inputfile)):
                raise flask.abort(404)

            if inputfile.metadata:
                headers = inputfile.metadata.httpheaders()
                mimetype = inputfile.metadata.mimetype
            else:
                printdebug("No metadata found for input file " + str(inputfile))
                headers = {}
                mimetype = mimetypes.guess_type(str(inputfile))[0]
                if not mimetype: mimetype = 'application/octet-stream'
            try:
                printdebug("Returning input file " + str(inputfile) + " with mimetype " + mimetype)
                return withheaders(flask.Response( (line for line in inputfile) ), mimetype, headers )
            except UnicodeError:
                return flask.make_response("Input file " + str(inputfile) + " is not in the expected encoding! Make sure encodings for output templates service configuration file are accurate.",500)
            except FileNotFoundError:
                raise flask.abort(404)
            except IOError:
                raise flask.abort(404)

    @staticmethod
    def deleteinputfile(project, filename, credentials=None):
        """Delete an input file"""

        user, oauth_access_token = parsecredentials(credentials)
        filename = filename.replace("..","") #Simple security

        if len(filename) == 0:
            #Deleting all input files
            shutil.rmtree(Project.path(project, user) + 'input')
            os.makedirs(Project.path(project, user) + 'input') #re-add new input directory
            return "Deleted" #200
        elif os.path.isdir(Project.path(project, user) + filename):
            #Deleting specified directory
            shutil.rmtree(Project.path(project, user) + filename)
            return "Deleted" #200
        else:
            try:
                file = clam.common.data.CLAMInputFile(Project.path(project, user), filename)
            except:
                raise flask.abort(404)

            success = file.delete()
            if not success:
                raise flask.abort(404)
            else:
                msg = "Deleted"
                return withheaders(flask.make_response(msg),'text/plain', {'Content-Length': len(msg)}) #200

    @staticmethod
    def addinputfile_nofile(project, credentials=None):
        printdebug('Addinputfile_nofile' )
        return Project.addinputfile(project,'',credentials)

    @staticmethod
    def addinputfile(project, filename, credentials=None):
        """Add a new input file, this invokes the actual uploader"""


        user, oauth_access_token = parsecredentials(credentials)
        Project.create(project, user)
        postdata = flask.request.values

        if filename == '':
            #Handle inputsource
            printdebug('Addinputfile: checking for input source' )
            if 'inputsource' in postdata and postdata['inputsource']:
                inputsource = None
                inputtemplate = None
                for profile in settings.PROFILES:
                    for t in profile.input:
                        for s in t.inputsources:
                            if s.id == postdata['inputsource']:
                                inputsource = s
                                inputsource.inputtemplate = t.id
                                inputtemplate = t
                                break
                if not inputsource:
                    for s in settings.INPUTSOURCES:
                        if s.id == postdata['inputsource']:
                            inputsource = s
                if not inputsource:
                    return flask.make_response("No such inputsource exists",403)
                if not inputtemplate:
                    for profile in settings.PROFILES:
                        for t in profile.input:
                            if inputsource.inputtemplate == t.id:
                                inputtemplate = t
                if inputtemplate is None:
                    return flask.make_response("No input template found for inputsource",500)
                if inputsource.isfile():
                    if inputtemplate.filename:
                        filename = inputtemplate.filename
                    else:
                        filename = os.path.basename(inputsource.path)
                    xml = addfile(project, filename, user, {'inputsource': postdata['inputsource'], 'inputtemplate': inputtemplate.id}, inputsource)
                    return xml
                elif inputsource.isdir():
                    if inputtemplate.filename:
                        filename = inputtemplate.filename
                    for f in glob.glob(inputsource.path + "/*"):
                        if not inputtemplate.filename:
                            filename = os.path.basename(f)
                        if f[0] != '.':
                            tmpinputsource = clam.common.data.InputSource(id='tmp',label='tmp',path=f, metadata=inputsource.metadata)
                            addfile(project, filename, user, {'inputsource':'tmp', 'inputtemplate': inputtemplate.id}, tmpinputsource)
                            #WARNING: Output is dropped silently here!
                    return "" #200
                else:
                    assert False
            else:
                return flask.make_response("No filename or inputsource specified",403)
        else:
            #Simply forward to addfile
            return addfile(project,filename,user, postdata)




    @staticmethod
    def extract(project,filename, archivetype):
        #OBSOLETE?
        #namelist = None
        subfiles = []

        #return [ subfile for subfile in subfiles ] #return only the files that actually exist


def addfile(project, filename, user, postdata, inputsource=None,returntype='xml'):
    """Add a new input file, this invokes the actual uploader"""

    inputtemplate_id = flask.request.headers.get('Inputtemplate','')
    inputtemplate = None
    metadata = None


    printdebug('Handling addfile, postdata contains fields ' + ",".join(postdata.keys()) )

    if 'inputtemplate' in postdata:
        inputtemplate_id = postdata['inputtemplate']

    if inputtemplate_id:
        #An input template must always be provided
        for profile in settings.PROFILES:
            for t in profile.input:
                if t.id == inputtemplate_id:
                    inputtemplate = t
        if not inputtemplate:
            #Inputtemplate not found, send 404
            printlog("Specified inputtemplate (" + inputtemplate_id + ") not found!")
            return flask.make_response("Specified inputtemplate (" + inputtemplate_id + ") not found!",404)
        printdebug('Inputtemplate explicitly provided: ' + inputtemplate.id )
    if not inputtemplate:
        #See if an inputtemplate is explicitly specified in the filename
        printdebug('Attempting to determine input template from filename ' + filename )
        if '/' in filename.strip('/'):
            raw = filename.split('/')
            inputtemplate = None
            for profile in settings.PROFILES:
                for it in profile.input:
                    if it.id == raw[0]:
                        inputtemplate = it
                        break
            if inputtemplate:
                filename = raw[1]
    if not inputtemplate:
        #Check if the specified filename can be uniquely associated with an inputtemplate
        for profile in settings.PROFILES:
            for t in profile.input:
                if t.filename == filename:
                    if inputtemplate:
                        #we found another one, not unique!! reset and break
                        inputtemplate = None
                        break
                    else:
                        #good, we found one, don't break cause we want to make sure there is only one
                        inputtemplate = t
        if not inputtemplate:
            printlog("No inputtemplate specified and filename " + filename + " does not uniquely match with any inputtemplate!")
            return flask.make_response("No inputtemplate specified nor auto-detected for filename " + filename + "!",404)



    #See if other previously uploaded input files use this inputtemplate
    if inputtemplate.unique:
        nextseq = 0 #unique
    else:
        nextseq = 1 #will hold the next sequence number for this inputtemplate (in multi-mode only)

    for seq, inputfile in Project.inputindexbytemplate(project, user, inputtemplate):
        if inputtemplate.unique:
            return flask.make_response("You have already submitted a file of this type, you can only submit one. Delete it first. (Inputtemplate=" + inputtemplate.id + ", unique=True)",403) #(it will have to be explicitly deleted by the client first)
        else:
            if seq >= nextseq:
                nextseq = seq + 1 #next available sequence number


    if not filename: #Actually, I don't think this can occur at this stage, but we'll leave it in to be sure
        if inputtemplate.filename:
            filename = inputtemplate.filename
        elif inputtemplate.extension:
            filename = str(nextseq) +'-' + str("%034x" % random.getrandbits(128)) + '.' + inputtemplate.extension
        else:
            filename = str(nextseq) +'-' + str("%034x" % random.getrandbits(128))

    #Make sure filename matches (only if not an archive)
    if inputtemplate.acceptarchive and (filename[-7:].lower() == '.tar.gz' or filename[-8:].lower() == '.tar.bz2' or filename[-4:].lower() == '.zip'):
        pass
    else:
        if inputtemplate.filename:
            if filename != inputtemplate.filename:
                filename = inputtemplate.filename
                #return flask.make_response("Specified filename must the filename dictated by the inputtemplate, which is " + inputtemplate.filename)
            #TODO LATER: add support for calling this with an actual number instead of #
        if inputtemplate.extension:
            if filename[-len(inputtemplate.extension) - 1:].lower() == '.' + inputtemplate.extension.lower():
                #good, extension matches (case independent). Let's just make sure the case is as defined exactly by the inputtemplate
                filename = filename[:-len(inputtemplate.extension) - 1] +  '.' + inputtemplate.extension
            else:
                filename = filename +  '.' + inputtemplate.extension
                #return flask.make_response("Specified filename does not have the extension dictated by the inputtemplate ("+inputtemplate.extension+")") #403

    if inputtemplate.onlyinputsource and (not 'inputsource' in postdata or not postdata['inputsource']):
        return flask.make_response("Adding files for this inputtemplate must proceed through inputsource",403) #403

    if 'converter' in postdata and postdata['converter'] and not postdata['converter'] in [ x.id for x in inputtemplate.converters]:
            return flask.make_response("Invalid converter specified: " + postdata['converter'],403) #403

    #Make sure the filename is secure
    validfilename = True
    DISALLOWED = ('/','&','|','<','>',';','"',"'","`","{","}","\n","\r","\b","\t")
    for c in filename:
        if c in DISALLOWED:
            validfilename = False
            break

    if not validfilename:
        return flask.make_response("Filename contains invalid symbols! Do not use /,&,|,<,>,',`,\",{,} or ;",403) #403


    #Create the project (no effect if already exists)
    Project.create(project, user)


    printdebug("(Obtaining filename for uploaded file)")
    head = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
    head += "<clamupload>\n"
    if 'file' in flask.request.files:
        printlog("Adding client-side file " + flask.request.files['file'].filename + " to input files")
        sourcefile = flask.request.files['file'].filename
    elif 'url' in postdata and postdata['url']:
        #Download from URL
        printlog("Adding web-based URL " + postdata['url'] + " to input files")
        sourcefile = os.path.basename(postdata['url'])
    elif 'contents' in postdata and postdata['contents']:
        #In message
        printlog("Adding file " + filename + " with explicitly provided contents to input files")
        sourcefile = "editor"
    elif 'inputsource' in postdata and postdata['inputsource']:
        printlog("Adding file " + filename + " from preinstalled data to input files")
        if not inputsource:
            inputsource = None
            for s in inputtemplate.inputsources:
                if s.id.lower() == postdata['inputsource'].lower():
                    inputsource = s
            if not inputsource:
                return flask.make_response("Specified inputsource '" + postdata['inputsource'] + "' does not exist for inputtemplate '"+inputtemplate.id+"'",403)
        sourcefile = os.path.basename(inputsource.path)
    elif 'accesstoken' in postdata and 'filename' in postdata:
        #XHR POST, data in body
        printlog("Adding client-side file " + filename + " to input files. Uploaded using XHR POST")
        sourcefile = postdata['filename']
    else:
        return flask.make_response("No file, url or contents specified!",403)




    #============================ Generate metadata ========================================
    printdebug('(Generating and validating metadata)')
    if 'metafile' in flask.request.files:  #and (not isinstance(postdata['metafile'], dict) or len(postdata['metafile']) > 0)):
        #an explicit metadata file was provided, upload it:
        printlog("Metadata explicitly provided in file, uploading...")
        #Upload file from client to server
        metafile = Project.path(project, user) + 'input/.' + filename + '.METADATA'
        flask.request.files['metafile'].save(metafile)
        try:
            with io.open(metafile,'r',encoding='utf-8') as f:
                metadata = clam.common.data.CLAMMetaData.fromxml(f.read())
            errors, parameters = inputtemplate.validate(metadata, user)
            validmeta = True
        except Exception as e:
            printlog("Uploaded metadata is invalid! " + str(e))
            metadata = None
            errors = True
            parameters = []
            validmeta = False
    elif 'metadata' in postdata and postdata['metadata']:
        printlog("Metadata explicitly provided in message, uploading...")
        try:
            metadata = clam.common.data.CLAMMetaData.fromxml(postdata['metadata'])
            errors, parameters = inputtemplate.validate(metadata, user)
            validmeta = True
        except:
            printlog("Uploaded metadata is invalid!")
            metadata = None
            errors = True
            parameters = []
            validmeta = False
    elif 'inputsource' in postdata and postdata['inputsource']:
        printlog("Getting metadata from inputsource, uploading...")
        if inputsource.metadata:
            printlog("DEBUG: Validating metadata from inputsource")
            metadata = inputsource.metadata
            errors, parameters = inputtemplate.validate(metadata, user)
            validmeta = True
        else:
            printlog("DEBUG: No metadata provided with inputsource, looking for metadata files..")
            metafilename = os.path.dirname(inputsource.path)
            if metafilename: metafilename += '/'
            metafilename += '.' + os.path.basename(inputsource.path) + '.METADATA'
            if os.path.exists(metafilename):
                try:
                    metadata = clam.common.data.CLAMMetaData.fromxml(open(metafilename,'r').readlines())
                    errors, parameters = inputtemplate.validate(metadata, user)
                    validmeta = True
                except:
                    printlog("Uploaded metadata is invalid!")
                    metadata = None
                    errors = True
                    parameters = []
                    validmeta = False
            else:
                 flask.make_response("No metadata found nor specified for inputsource " + inputsource.id ,500)
    else:
        errors, parameters = inputtemplate.validate(postdata, user)
        validmeta = True #will be checked later


    #  ----------- Check if archive are allowed -------------
    archive = False
    addedfiles = []
    if not errors and inputtemplate.acceptarchive:
        printdebug('(Archive test)')
        # -------- Are we an archive? If so, determine what kind
        archivetype = None
        if 'file' in flask.request.files:
            uploadname = sourcefile.lower()
            archivetype = None
            if uploadname[-4:] == '.zip':
                archivetype = 'zip'
            elif uploadname[-7:] == '.tar.gz':
                archivetype = 'tar.gz'
            elif uploadname[-4:] == '.tar':
                archivetype = 'tar'
            elif uploadname[-8:] == '.tar.bz2':
                archivetype = 'tar.bz2'
            xhrpost = False
        elif 'accesstoken' in postdata and 'filename' in postdata:
            xhrpost = True
            if postdata['filename'][-7:].lower() == '.tar.gz':
                uploadname = sourcefile.lower()
                archivetype = 'tar.gz'
            elif postdata['filename'][-8:].lower() == '.tar.bz2':
                uploadname = sourcefile.lower()
                archivetype = 'tar.bz2'
            elif postdata['filename'][-4:].lower() == '.tar':
                uploadname = sourcefile.lower()
                archivetype = 'tar'
            elif postdata['filename'][-4:].lower() == '.zip':
                uploadname = sourcefile.lower()
                archivetype = 'zip'

        if archivetype:
            # =============== upload archive ======================
            #random name
            archive = "%032x" % random.getrandbits(128) + '.' + archivetype

            #Upload file from client to server
            printdebug('(Archive transfer starting)')
            if not xhrpost:
                flask.request.files['file'].save(Project.path(project,user) + archive)
            elif xhrpost:
                f = open(Project.path(project,user) + archive,'wb') #TODO: test
                while True:
                    chunk = flask.request.stream.read(16384)
                    if chunk:
                        f.write(chunk)
                    else:
                        break
                f.close()
            printdebug('(Archive transfer completed)')
            # =============== Extract archive ======================

            #Determine extraction command
            if archivetype == 'zip':
                cmd = 'unzip -u'
            elif archivetype == 'tar':
                cmd = 'tar -xvf'
            elif archivetype == 'tar.gz':
                cmd = 'tar -xvzf'
            elif archivetype == 'tar.bz2':
                cmd = 'tar -xvjf'
            else:
                raise Exception("Invalid archive format: " + archivetype) #invalid archive, shouldn't happen

            #invoke extractor
            printlog("Extracting '" + archive + "'" )
            try:
                process = subprocess.Popen(cmd + " " + archive, cwd=Project.path(project,user), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            except:
                flask.make_response("Unable to extract archive",500)
            out, _ = process.communicate() #waits for process to end

            if sys.version < '3':
                if isinstance(out, str):
                    out = unicode(out,'utf-8') #pylint: disable=undefined-variable
            else:
                if isinstance(out, bytes):
                    out = str(out,'utf-8')

            #Read filename results

            firstline = True
            for line in out.split("\n"):
                line = line.strip()
                if line:
                    printdebug('(Extraction output: ' + line+')')
                    subfile = None
                    if archivetype[0:3] == 'tar':
                        subfile = line
                    elif archivetype == 'zip' and not firstline: #firstline contains archive name itself, skip it
                        colon = line.find(":")
                        if colon:
                            subfile =  line[colon + 1:].strip()
                    if subfile and os.path.isfile(Project.path(project, user) + subfile):
                        subfile_newname = clam.common.data.resolveinputfilename(os.path.basename(subfile), parameters, inputtemplate, nextseq+len(addedfiles), project)
                        printdebug('(Extracted file ' + subfile + ', moving to input/' + subfile_newname+')')
                        os.rename(Project.path(project, user) + subfile, Project.path(project, user) + 'input/' +  subfile_newname)
                        addedfiles.append(subfile_newname)
                firstline = False

            #all done, remove archive
            os.unlink(Project.path(project, user) + archive)

    if not archive:
        addedfiles = [clam.common.data.resolveinputfilename(filename, parameters, inputtemplate, nextseq, project)]

    fatalerror = None

    jsonoutput = {'success': False if errors else True, 'isarchive': archive}


    output = head
    for filename in addedfiles:
        output += "<upload source=\""+sourcefile +"\" filename=\""+filename+"\" inputtemplate=\"" + inputtemplate.id + "\" templatelabel=\""+inputtemplate.label+"\">\n"

        if not errors:
            output += "<parameters errors=\"no\">"
        else:
            output += "<parameters errors=\"yes\">"
            jsonoutput['error'] = 'There were parameter errors, file not uploaded: '
        for parameter in parameters:
            output += parameter.xml()
            if parameter.error:
                jsonoutput['error'] += parameter.error + ". "
        output += "</parameters>"



        if not errors:
            if not archive:
                #============================ Transfer file ========================================
                printdebug('(Start file transfer: ' +  Project.path(project, user) + 'input/' + filename+' )')
                if 'file' in flask.request.files:
                    printdebug('(Receiving data by uploading file)')
                    #Upload file from client to server
                    flask.request.files['file'].save(Project.path(project, user) + 'input/' + filename)
                elif 'url' in postdata and postdata['url']:
                    printdebug('(Receiving data via url)')
                    #Download file from 3rd party server to CLAM server
                    try:
                        r = requests.get(postdata['url'])
                    except:
                        raise flask.abort(404)
                    if not (r.status_code >= 200 and r.status_code < 300):
                        raise flask.abort(404)

                    CHUNK = 16 * 1024
                    f = open(Project.path(project, user) + 'input/' + filename,'wb')
                    for chunk in r.iter_content(chunk_size=CHUNK):
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            f.flush()
                    f.close()
                elif 'inputsource' in postdata and postdata['inputsource']:
                    #Copy (symlink!) from preinstalled data
                    printdebug('(Creating symlink to file ' + inputsource.path + ' <- ' + Project.path(project,user) + '/input/ ' + filename + ')')
                    os.symlink(inputsource.path, Project.path(project, user) + 'input/' + filename)
                elif 'contents' in postdata and postdata['contents']:
                    printdebug('(Receiving data via from contents variable)')
                    #grab encoding
                    encoding = 'utf-8'
                    for p in parameters:
                        if p.id == 'encoding':
                            encoding = p.value
                    #Contents passed in POST message itself
                    try:
                        f = io.open(Project.path(project, user) + 'input/' + filename,'w',encoding=encoding)
                        f.write(postdata['contents'])
                        f.close()
                    except UnicodeError:
                        return flask.make_response("Input file " + str(filename) + " is not in the expected encoding!",403)
                elif 'accesstoken' in postdata and 'filename' in postdata:
                    printdebug('(Receiving data directly from post body)')
                    f = open(Project.path(project,user) + 'input/' + filename,'wb') #TODO: test
                    while True:
                        chunk = flask.request.stream.read(16384)
                        if chunk:
                            f.write(chunk)
                        else:
                            break
                    f.close()

                printdebug('(File transfer completed)')



            #Create a file object
            file = clam.common.data.CLAMInputFile(Project.path(project, user), filename, False) #get CLAMInputFile without metadata (chicken-egg problem, this does not read the actual file contents!



            #============== Generate metadata ==============

            metadataerror = None
            if not metadata and not errors: #check if it has not already been set in another stage
                printdebug('(Generating metadata)')
                #for newly generated metadata
                try:
                    #Now we generate the actual metadata object (unsaved yet though). We pass our earlier validation results to prevent computing it again
                    validmeta, metadata, parameters = inputtemplate.generate(file, (errors, parameters ))
                    if validmeta:
                        #And we tie it to the CLAMFile object
                        file.metadata = metadata
                        #Add inputtemplate ID to metadata
                        metadata.inputtemplate = inputtemplate.id
                    else:
                        metadataerror = "Undefined error"
                except ValueError as msg:
                    validmeta = False
                    metadataerror = msg
                except KeyError as msg:
                    validmeta = False
                    metadataerror = msg
            elif validmeta:
                #for explicitly uploaded metadata
                metadata.file = file
                file.metadata = metadata
                metadata.inputtemplate = inputtemplate.id

            if metadataerror:
                printdebug('(Metadata could not be generated, ' + str(metadataerror) + ',  this usually indicated an error in service configuration)')
                #output += "<metadataerror />" #This usually indicates an error in service configuration!
                fatalerror = "<error type=\"metadataerror\">Metadata could not be generated for " + filename + ": " + str(metadataerror) + " (this usually indicates an error in service configuration!)</error>"
                jsonoutput['error'] = "Metadata could not be generated! " + str(metadataerror) + "  (this usually indicates an error in service configuration!)"
            elif validmeta:
                #=========== Convert the uploaded file (if requested) ==============

                conversionerror = False
                if 'converter' in postdata and postdata['converter']:
                    for c in inputtemplate.converters:
                        if c.id == postdata['converter']:
                            converter = c
                            break
                    if converter: #(should always be found, error already provided earlier if not)
                        printdebug('(Invoking converter)')
                        try:
                            success = converter.convertforinput(Project.path(project, user) + 'input/' + filename, metadata)
                        except:
                            success = False
                        if not success:
                            conversionerror = True
                            fatalerror = "<error type=\"conversion\">The file " + xmlescape(filename) + " could not be converted</error>"
                            jsonoutput['error'] = "The file could not be converted"
                            jsonoutput['success'] = False

                #====================== Validate the file itself ====================
                if not conversionerror:
                    valid = file.validate()

                    if valid:
                        printdebug('(Validation ok)')
                        output += "<valid>yes</valid>"

                        #Great! Everything ok, save metadata
                        metadata.save(Project.path(project, user) + 'input/' + file.metafilename())

                        #And create symbolic link for inputtemplates
                        linkfilename = os.path.dirname(filename)
                        if linkfilename: linkfilename += '/'
                        linkfilename += '.' + os.path.basename(filename) + '.INPUTTEMPLATE' + '.' + inputtemplate.id + '.' + str(nextseq)
                        os.symlink(Project.path(project, user) + 'input/' + filename, Project.path(project, user) + 'input/' + linkfilename)
                    else:
                        printdebug('(Validation error)')
                        #Too bad, everything worked out but the file itself doesn't validate.
                        #output += "<valid>no</valid>"
                        fatalerror = "<error type=\"validation\">The file " + xmlescape(filename) + " did not validate, it is not in the proper expected format.</error>"
                        jsonoutput['errors'] = "The file " + filename.replace("'","") + " did not validate, it is not in the proper expected format."
                        jsonoutput['success'] = False
                        #remove upload
                        os.unlink(Project.path(project, user) + 'input/' + filename)


        output += "</upload>\n"

    output += "</clamupload>"



    if fatalerror:
        #fatal error return error message with 403 code
        printlog('Fatal Error during upload: ' + fatalerror)
        return flask.make_response(head + fatalerror,403)
    elif errors:
        #parameter errors, return XML output with 403 code
        printdebug('There were parameter errors during upload!')
        return flask.make_response(output,403)
    elif returntype == 'xml':
        printdebug('Returning xml')
        return withheaders(flask.make_response(output), 'text/xml')
    elif returntype == 'json':
        printdebug('Returning json')
        #everything ok, return JSON output (caller decides)
        jsonoutput['xml'] = output #embed XML in JSON for complete client-side processing
        return withheaders(flask.make_response(json.dumps(jsonoutput)), 'application/json')
    else:
        printdebug('Invalid return type')
        raise Exception("invalid return type")




def interfacedata(): #no auth
    inputtemplates_mem = []
    inputtemplates = []
    for profile in settings.PROFILES:
        for inputtemplate in profile.input:
            if not inputtemplate in inputtemplates: #no duplicates
                inputtemplates_mem.append(inputtemplate)
                inputtemplates.append( inputtemplate.json() )

    return withheaders(flask.make_response("systemid = '"+ settings.SYSTEM_ID + "'; baseurl = '" + getrooturl() + "';\n inputtemplates = [ " + ",".join(inputtemplates) + " ];"), 'text/javascript')

def foliaxsl():
    if foliatools is not None:
        return withheaders(flask.make_response(io.open(foliatools.__path__[0] + '/folia2html.xsl','r',encoding='utf-8').read()),'text/xsl')
    else:
        return flask.make_response("folia.xsl is not available, no FoLiA Tools installed on this server",404)


def styledata():
    return withheaders(flask.make_response(io.open(settings.CLAMDIR + '/style/' + settings.STYLE + '.css','r',encoding='utf-8').read()),'text/css')


def uploader(project, credentials=None):
    """The Uploader is intended for the Fine Uploader used in the web application (or similar frontend), it is not intended for proper RESTful communication. Will return JSON compatible with Fine Uploader rather than CLAM Upload XML. Unfortunately, normal digest authentication does not work well with the uploader, so we implement a simple key check based on hashed username, projectname and a secret key that is communicated as a JS variable in the interface ."""
    postdata = flask.request.values
    if 'user' in postdata:
        user = postdata['user']
    else:
        user = 'anonymous'
    if 'filename' in postdata:
        filename = postdata['filename']
    else:
        printdebug('No filename passed')
        return "{success: false, error: 'No filename passed'}"
    if 'accesstoken' in postdata:
        accesstoken = postdata['accesstoken']
    else:
        return withheaders(flask.make_response("{success: false, error: 'No accesstoken given'}"),'application/json')
    if accesstoken != Project.getaccesstoken(user,project):
        return withheaders(flask.make_response("{success: false, error: 'Invalid accesstoken given'}"),'application/json')
    if not os.path.exists(Project.path(project, user)):
        return withheaders(flask.make_response("{success: false, error: 'Destination does not exist'}"),'application/json')
    else:
        return addfile(project,filename,user, postdata,None, 'json' )




class ActionHandler(object):

    @staticmethod
    def find_action( action_id, method):
        for action in settings.ACTIONS:
            if action.id == action.id and (not action.method or method == action.method):
                return action
        return flask.make_response("Action does not exist",404)

    @staticmethod
    def collect_parameters(action):
        data = flask.request.values
        params = []
        for parameter in action.parameters:
            if not parameter.id in data:
                return flask.make_response("Missing parameter: " + parameter.id,403)
            else:
                if parameter.paramflag:
                    flag = parameter.paramflag
                else:
                    flag = None
                if not parameter.set(data[parameter.id]):
                    return flask.make_response("Invalid value for parameter " + parameter.id + ": " + parameter.error,403)
                else:
                    params.append( ( flag, parameter.value) )
        return params


    @staticmethod
    def do( action_id, method, user="anonymous", oauth_access_token=""):
        action = ActionHandler.find_action(action_id, 'GET')

        userdir =  settings.ROOT + "projects/" + user + '/'

        if action.command:
            parameters = ""
            for flag, value in ActionHandler.collect_parameters(action):
                if parameters: parameters += " "
                if flag: parameters += flag + " "

                if sys.version[0] == '2':
                    if isinstance(value, unicode):#pylint: disable=undefined-variable
                        value = value.encode('utf-8')
                    elif not isinstance(value, str):
                        value = str(value)
                elif not isinstance(value, str):
                    value = str(value)
                if value: parameters += clam.common.data.shellsafe(value,'"')

            cmd = action.command
            cmd = cmd.replace('$PARAMETERS', parameters)
            cmd = cmd.replace('$USERNAME',user if user else "anonymous")
            cmd = cmd.replace('$OAUTH_ACCESS_TOKEN',oauth_access_token if oauth_access_token else "")
            #everything should be shell-safe now

            #run the action
            pythonpath = ''
            try:
                pythonpath = ':'.join(settings.DISPATCHER_PYTHONPATH)
            except:
                pass
            if pythonpath:
                pythonpath = os.path.dirname(settings.__file__) + ':' + pythonpath
            else:
                pythonpath = os.path.dirname(settings.__file__)

            cmd = settings.DISPATCHER + ' ' + pythonpath + ' ' + settingsmodule + ' NONE ' + cmd
            if settings.REMOTEHOST:
                if settings.REMOTEUSER:
                    cmd = "ssh -o NumberOfPasswordPrompts=0 " + settings.REMOTEUSER + "@" + settings.REMOTEHOST + " " + cmd
                else:
                    cmd = "ssh -o NumberOfPasswordPrompts=0 " + settings.REMOTEHOST + " " + cmd
            printlog("Starting dispatcher " +  settings.DISPATCHER + " for action " + action_id + " with " + action.command + ": " + repr(cmd) + " ..." )
            process = subprocess.Popen(cmd,cwd=userdir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process:
                printlog("Waiting for dispatcher (pid " + str(process.pid) + ") to finish" )
                stdoutdata, stderrdata = process.communicate()
                if process.returncode in action.returncodes200:
                    return withheaders(stdoutdata,action.mimetype) #200
                elif process.returncode in action.returncodes403:
                    return withheaders(flask.make_response(stdoutdata,403), action.mimetype)
                elif process.returncode in action.returncodes404:
                    return withheaders(flask.make_response(stdoutdata, 404), action.mimetype)
                else:
                    return flask.make_response("Process for action " +  action_id + " failed\n" + stderrdata,500)
            else:
                return flask.make_response("Unable to launch process",500)
        elif action.function:
            args = [ x[1] for x in  ActionHandler.collect_parameters(action) ]
            try:
                r = action.function(*args) #200
            except Exception as e:
                if isinstance(e, werkzeug.exceptions.HTTPException):
                    raise
                else:
                    return flask.make_response(e,500)
            if not isinstance(r, flask.Response):
                return withheaders(flask.make_response(r), action.mimetype)
            else:
                return r
        else:
            raise Exception("No command or function defined for action " + action_id)

    @staticmethod
    def do_auth(action_id, method, credentials=None):
        user, oauth_access_token = parsecredentials(credentials)
        return ActionHandler.do(action_id, method, user, oauth_access_token)

    @staticmethod
    def run(action_id, method):
        #check whether the action requires authentication or allows anonymous users:
        action = ActionHandler.find_action(action_id, method)
        if action.allowanonymous:
            user = "anonymous"
            oauth_access_token = ""
            return ActionHandler.do(action_id, method,user,oauth_access_token)
        else:
            return ActionHandler.do_auth(action_id, method)


    @staticmethod
    def GET(action_id):
        return ActionHandler.run(action_id, 'GET')

    @staticmethod
    def POST(action_id):
        return ActionHandler.run(action_id, 'POST')

    @staticmethod
    def PUT(action_id):
        return ActionHandler.run(action_id, 'PUT')

    @staticmethod
    def DELETE(action_id):
        return ActionHandler.run(action_id, 'DELETE')


def sufficientresources():
    if settings.REQUIREMEMORY > 0:
        if not os.path.exists('/proc/meminfo'):
            printlog("WARNING: No /proc/meminfo available on your system! Not Linux? Skipping memory requirement check!")
        else:
            memfree = cached = 0
            f = open('/proc/meminfo')
            for line in f:
                if line[0:8] == "MemFree:":
                    memfree = float(line[9:].replace('kB','').strip()) #in kB
                if line[0:8] == "Cached:":
                    cached = float(line[9:].replace('kB','').strip()) #in kB
            f.close()
            if settings.REQUIREMEMORY * 1024 > memfree + cached:
                return False, str(settings.REQUIREMEMORY * 1024) + " kB memory is required but only " + str(memfree + cached) + " is available."
    if settings.MAXLOADAVG > 0:
        if not os.path.exists('/proc/loadavg'):
            printlog("WARNING: No /proc/loadavg available on your system! Not Linux? Skipping load average check!")
        else:
            f = open('/proc/loadavg')
            line = f.readline()
            loadavg = float(line.split(' ')[0])
            f.close()
            if settings.MAXLOADAVG < loadavg:
                return False, "System load too high: " + str(loadavg) + ", max is " + str(settings.MAXLOADAVG)
    if settings.MINDISKSPACE and settings.DISK:
        dffile = '/tmp/df.' + str("%034x" % random.getrandbits(128))
        ret = os.system('df -mP ' + settings.DISK + " | gawk '{ print $4; }'  > " + dffile)
        if ret == 0:
            try:
                f = open(dffile,'r')
                free = int(f.readlines()[-1])
                f.close()
                if free < settings.MINDISKSPACE:
                    os.unlink(dffile)
                    return False, "Not enough diskspace, " + str(free) + " MB free, need at least " + str(settings.MINDISKSPACE) + " MB"
            except:
                printlog("WARNING: df " + settings.DISK + " failed (unexpected format). Skipping disk space check!")
                os.unlink(dffile)

        else:
            printlog("WARNING: df " + settings.DISK + " failed. Skipping disk space check!")
    return True, ""



def usage():
        print( "Syntax: clamservice.py [options] clam.config.yoursystem",file=sys.stderr)
        print("Options:",file=sys.stderr)
        print("\t-d            - Enable debug mode",file=sys.stderr)
        print("\t-H [hostname] - Hostname",file=sys.stderr)
        print("\t-p [port]     - Port",file=sys.stderr)
        print("\t-u [url]      - Force URL",file=sys.stderr)
        print("\t-h            - This help message",file=sys.stderr)
        print("\t-P [path]     - Python Path from which the settings module can be imported",file=sys.stderr)
        print("\t-v            - Version information",file=sys.stderr)
        print("(Note: Running clamservice directly from the command line uses the built-in",file=sys.stderr)
        print("web-server. This is great for development purposes but not recommended",file=sys.stderr)
        print("for production use. Use the WSGI interface with for instance Apache instead.)",file=sys.stderr)

class CLAMService(object):
    """CLAMService is the actual service object. See the documentation for a full specification of the REST interface."""

    def __init__(self, mode = 'debug'):
        global VERSION
        printlog("Starting CLAM WebService, version " + str(VERSION) + " ...")
        if not settings.ROOT or not os.path.isdir(settings.ROOT):
            error("Specified root path " + settings.ROOT + " not found")
        elif settings.COMMAND and (not settings.COMMAND.split(" ")[0] or not os.path.exists( settings.COMMAND.split(" ")[0])):
            error("Specified command " + settings.COMMAND.split(" ")[0] + " not found")
        elif settings.COMMAND and not os.access(settings.COMMAND.split(" ")[0], os.X_OK):
            if settings.COMMAND.split(" ")[0][-3:] == ".py" and sys.executable:
                if UWSGI:
                    if 'virtualenv' in uwsgi.opt and uwsgi.opt['virtualenv']:
                        base = uwsgi.opt['virtualenv']
                        if sys.version >= '3' and isinstance(base, bytes):
                            base = str(base, 'utf-8')
                        interpreter = base + '/bin/python'
                    elif 'home' in uwsgi.opt and uwsgi.opt['home']:
                        base = uwsgi.opt['home']
                        if sys.version >= '3' and isinstance(base, bytes):
                            base = str(base, 'utf-8')
                        interpreter = uwsgi.opt['home'] + '/bin/python'
                    else:
                        if sys.version > '3':
                            interpreter = 'python3'
                        else:
                            interpreter = 'python'
                else:
                    interpreter = sys.executable
                settings.COMMAND = interpreter + " " + settings.COMMAND
            else:
                error("Specified command " + settings.COMMAND.split(" ")[0] + " is not executable")
        else:
            lastparameter = None
            try:
                for parametergroup, parameters in settings.PARAMETERS:
                    for parameter in parameters:
                        assert isinstance(parameter, clam.common.parameters.AbstractParameter)
                        lastparameter = parameter
            except AssertionError:
                msg = "Syntax error in parameter specification."
                if lastparameter:
                     msg += "Last part parameter: ", lastparameter.id
                error(msg)

        if settings.OAUTH:
            warning("*** Oauth Authentication is enabled. THIS IS NOT SECURE WITHOUT SSL! ***")
            self.auth = clam.common.auth.OAuth2(settings.OAUTH_CLIENT_ID, settings.OAUTH_ENCRYPTIONSECRET, settings.OAUTH_AUTH_URL, getrooturl() + '/login/', settings.OAUTH_AUTH_FUNCTION, settings.OAUTH_USERNAME_FUNCTION, printdebug=printdebug,scope=settings.OAUTH_SCOPE)
        elif settings.USERS:
            if settings.BASICAUTH:
                self.auth = clam.common.auth.HTTPBasicAuth(get_password=userdb_lookup_dict, realm=settings.REALM,debug=printdebug)
                warning("*** HTTP Basic Authentication is enabled. THIS IS NOT SECURE WITHOUT SSL! ***")
            else:
                self.auth = clam.common.auth.HTTPDigestAuth(settings.SESSIONDIR,get_password=userdb_lookup_dict, realm=settings.REALM,debug=printdebug)
        elif settings.USERS_MYSQL:
            validate_users_mysql()
            if settings.BASICAUTH:
                self.auth = clam.common.auth.HTTPBasicAuth(get_password=userdb_lookup_mysql, realm=settings.REALM,debug=printdebug)
                warning("*** HTTP Basic Authentication is enabled. THIS IS NOT SECURE WITHOUT SSL! ***")
            else:
                self.auth = clam.common.auth.HTTPDigestAuth(settings.SESSIONDIR, get_password=userdb_lookup_mysql,realm=settings.REALM,debug=printdebug)
        elif settings.PREAUTHHEADER:
            warning("*** Forwarded Authentication is enabled. THIS IS NOT SECURE WITHOUT A PROPERLY CONFIGURED AUTHENTICATION PROVIDER! ***")
            self.auth = clam.common.auth.ForwardedAuth(settings.PREAUTHHEADER)
        else:
            warning("*** NO AUTHENTICATION ENABLED!!! This is strongly discouraged in production environments! ***")
            self.auth = clam.common.auth.NoAuth()



        self.service = flask.Flask("clam")
        self.service.secret_key = settings.SECRET_KEY
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/', 'index', self.auth.require_login(index), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/info/', 'info', info, methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/login/', 'login', Login.GET, methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/logout/', 'logout', self.auth.require_login(Logout.GET), methods=['GET'] )

        #versions without trailing slash so no automatic 301 redirect is needed
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/info', 'info2', info, methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/login', 'login2', Login.GET, methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/logout', 'logout2', self.auth.require_login(Logout.GET), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/actions/<actionid>', 'action_get2', self.auth.require_login(ActionHandler.GET), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/actions/<actionid>', 'action_post2', self.auth.require_login(ActionHandler.POST), methods=['POST'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/actions/<actionid>', 'action_put2', self.auth.require_login(ActionHandler.PUT), methods=['PUT'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/actions/<actionid>', 'action_delete2', self.auth.require_login(ActionHandler.DELETE), methods=['DELETE'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/status', 'project_status_json2', Project.status_json, methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/upload', 'project_uploader2', uploader, methods=['POST'] ) #has it's own login mechanism
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>', 'project_get2', self.auth.require_login(Project.get), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>', 'project_start2', self.auth.require_login(Project.start), methods=['POST'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>', 'project_new2', self.auth.require_login(Project.new), methods=['PUT'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>', 'project_delete2', self.auth.require_login(Project.delete), methods=['DELETE'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/zip', 'project_download_zip2', self.auth.require_login(Project.download_zip), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/gz', 'project_download_targz2', self.auth.require_login(Project.download_targz), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/bz2', 'project_download_tarbz22', self.auth.require_login(Project.download_tarbz2), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output', 'project_download_zip3', self.auth.require_login(Project.download_zip), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/input', 'project_addinputfile3', self.auth.require_login(Project.addinputfile_nofile), methods=['POST','GET'] )

        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/data.js', 'interfacedata', interfacedata, methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/style.css', 'styledata', styledata, methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/admin/', 'adminindex', self.auth.require_login(Admin.index), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/admin/download/<targetuser>/<project>/<type>/<filename>/', 'admindownloader', self.auth.require_login(Admin.downloader), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/admin/<command>/<targetuser>/<project>/', 'adminhandler', self.auth.require_login(Admin.handler), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/actions/<actionid>/', 'action_get', self.auth.require_login(ActionHandler.GET), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/actions/<actionid>/', 'action_post', self.auth.require_login(ActionHandler.POST), methods=['POST'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/actions/<actionid>/', 'action_put', self.auth.require_login(ActionHandler.PUT), methods=['PUT'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/actions/<actionid>/', 'action_delete', self.auth.require_login(ActionHandler.DELETE), methods=['DELETE'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/zip/', 'project_download_zip', self.auth.require_login(Project.download_zip), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/gz/', 'project_download_targz', self.auth.require_login(Project.download_targz), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/bz2/', 'project_download_tarbz2', self.auth.require_login(Project.download_tarbz2), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/<path:filename>', 'project_getoutputfile', self.auth.require_login(Project.getoutputfile), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/<path:filename>', 'project_deleteoutputfile', self.auth.require_login(Project.deleteoutputfile), methods=['DELETE'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/', 'project_download_zip4', self.auth.require_login(Project.download_zip), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/output/', 'project_deletealloutput', self.auth.require_login(Project.deletealloutput), methods=['DELETE'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/input/<path:filename>', 'project_getinputfile', self.auth.require_login(Project.getinputfile), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/input/<path:filename>', 'project_deleteinputfile', self.auth.require_login(Project.deleteinputfile), methods=['DELETE'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/input/<path:filename>', 'project_addinputfile', self.auth.require_login(Project.addinputfile), methods=['POST'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/input/', 'project_addinputfile2', self.auth.require_login(Project.addinputfile_nofile), methods=['POST','GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/status/', 'project_status_json', Project.status_json, methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/upload/', 'project_uploader', uploader, methods=['POST'] ) #has it's own login mechanism
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/', 'project_get', self.auth.require_login(Project.get), methods=['GET'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/', 'project_start', self.auth.require_login(Project.start), methods=['POST'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/', 'project_new', self.auth.require_login(Project.new), methods=['PUT'] )
        self.service.add_url_rule(settings.STANDALONEURLPREFIX + '/<project>/', 'project_delete', self.auth.require_login(Project.delete), methods=['DELETE'] )


        self.mode = mode
        if self.mode != 'wsgi' and (settings.OAUTH or settings.PREAUTHHEADER or settings.BASICAUTH):
            warning("*** YOU ARE RUNNING THE DEVELOPMENT SERVER, THIS IS INSECURE WITH THE CONFIGURED AUTHENTICATION METHOD ***")
        printlog("Server available on http://" + settings.HOST + ":" + str(settings.PORT) +'/' + settings.URLPREFIX + ' (Make sure to use access CLAM using this exact URL and no alternative hostnames/IPs)')
        if settings.FORCEURL:
            printlog("Access using forced URL: " + settings.FORCEURL)

        if self.mode == 'wsgi':
            self.service.debug = DEBUG
        elif self.mode in ('standalone','debug'):
            self.service.debug = (mode == 'debug')
            self.service.run(host=settings.HOST,port=settings.PORT)
        else:
            raise Exception("Unknown mode: " + mode + ", specify 'wsgi', 'standalone' or 'debug'")

    @staticmethod
    def corpusindex():
            """Get list of pre-installed corpora"""
            corpora = []
            for f in glob.glob(settings.ROOT + "corpora/*"):
                if os.path.isdir(f):
                    corpora.append(os.path.basename(f))
            return corpora



def set_defaults():
    global LOG

    #Default settings
    settingkeys = dir(settings)

    settings.STANDALONEURLPREFIX = ''

    for s in ['SYSTEM_ID','SYSTEM_DESCRIPTION','SYSTEM_NAME','ROOT','COMMAND','PROFILES']:
        if not s in settingkeys:
            error("ERROR: Service configuration incomplete, missing setting: " + s)

    if 'ROOT' in settingkeys and settings.ROOT and not settings.ROOT[-1] == "/":
        settings.ROOT += "/" #append slash
    if not 'USERS' in settingkeys:
        settings.USERS = None
    if not 'ADMINS' in settingkeys:
        settings.ADMINS = []
    if not 'BASICAUTH' in settingkeys:
        settings.BASICAUTH = False #default is HTTP Digest
    if not 'PROJECTS_PUBLIC' in settingkeys:
        settings.PROJECTS_PUBLIC = True
    if not 'PROFILES' in settingkeys:
        settings.PROFILES = []
    if not 'INPUTSOURCES' in settingkeys:
        settings.INPUTSOURCES = []
    if not 'PORT' in settingkeys and not PORT:
        settings.PORT = 80
    if not 'HOST' in settingkeys and not HOST:
        settings.HOST = os.uname()[1]
    if not 'URLPREFIX' in settingkeys:
        settings.URLPREFIX = ''
    if not 'REQUIREMEMORY' in settingkeys:
        settings.REQUIREMEMORY = 0 #unlimited
    if not 'MAXLOADAVG' in settingkeys:
        settings.MAXLOADAVG = 0 #unlimited
    if not 'MINDISKSPACE' in settingkeys:
        if 'MINDISKFREE' in settingkeys:
            settings.MINDISKSPACE = settingkeys['MINDISKFREE']
        else:
            settings.MINDISKSPACE = 0
    if not 'DISK' in settingkeys:
        settings.DISK = None
    if not 'STYLE' in settingkeys:
        settings.STYLE = 'classic'
    if not 'CLAMDIR' in settingkeys:
        settings.CLAMDIR = os.path.dirname(os.path.abspath(__file__))
    if not 'DISPATCHER' in settingkeys:
        r = os.system('which clamdispatcher >/dev/null 2>/dev/null')
        if r == 0:
            settings.DISPATCHER = 'clamdispatcher'
        elif os.path.exists(settings.CLAMDIR + '/clamdispatcher.py') and stat.S_IXUSR & os.stat(settings.CLAMDIR + '/clamdispatcher.py')[stat.ST_MODE]:
            settings.DISPATCHER = settings.CLAMDIR + '/clamdispatcher.py'
        else:
            print("WARNING: clamdispatcher not found!!",file=sys.stderr)
            settings.DISPATCHER = 'clamdispatcher'
    if not 'REALM' in settingkeys:
        settings.REALM = settings.SYSTEM_ID
    if not 'DIGESTOPAQUE' in settingkeys:
        settings.DIGESTOPAQUE = "%032x" % random.getrandbits(128) #TODO: not used now
    if not 'OAUTH_ENCRYPTIONSECRET' in settingkeys:
        settings.OAUTH_ENCRYPTIONSECRET = None
    if not 'ENABLEWEBAPP' in settingkeys:
        settings.ENABLEWEBAPP = True
    if not 'REMOTEHOST' in settingkeys:
        settings.REMOTEHOST = None
    elif not 'REMOTEUSER' in settingkeys:
        settings.REMOTEUSER = None
    if not 'PREAUTHHEADER' in settingkeys:
        settings.PREAUTHHEADER = None     #The name of the header field containing the pre-authenticated username
    elif isinstance(settings.PREAUTHHEADER,str):
        settings.PREAUTHHEADER = settings.PREAUTHHEADER.split(' ')
    else:
        settings.PREAUTHHEADER = None
    if not 'USERS_MYSQL' in settingkeys:
        settings.USERS_MYSQL = None
    if not 'FORCEURL' in settingkeys:
        settings.FORCEURL = None
    if 'CLAMFORCEURL' in os.environ:
        settings.FORCEURL = os.environ['CLAMFORCEURL']
    if not 'PRIVATEACCESSTOKEN' in settingkeys:
        settings.PRIVATEACCESSTOKEN = "%032x" % random.getrandbits(128)
    if not 'OAUTH' in settingkeys:
        settings.OAUTH = False
    if not 'OAUTH_CLIENT_ID' in settingkeys:
        settings.OAUTH_CLIENT_ID = settings.SYSTEM_ID
    if not 'OAUTH_CLIENT_SECRET' in settingkeys:
        settings.OAUTH_CLIENT_SECRET = ""
    if not 'OAUTH_AUTH_URL' in settingkeys:
        settings.OAUTH_AUTH_URL = ""
    if not 'OAUTH_TOKEN_URL' in settingkeys:
        settings.OAUTH_TOKEN_URL = ""
    if not 'OAUTH_REVOKE_URL' in settingkeys:
        settings.OAUTH_REVOKE_URL = ""
    if not 'OAUTH_SCOPE' in settingkeys:
        settings.OAUTH_SCOPE = []
    if not 'OAUTH_USERNAME_FUNCTION' in settingkeys:
        settings.OAUTH_USERNAME_FUNCTION = None
    if not 'OAUTH_AUTH_FUNCTION' in settingkeys:
        settings.OAUTH_AUTH_FUNCTION = lambda oauthsession, authurl: oauthsession.authorization_url(authurl)
    if not 'SECRET_KEY' in settingkeys:
        print("WARNING: No explicit SECRET_KEY set in service configuration, generating one at random! This may cause problems with session persistence in production environments!" ,file=sys.stderr)
        settings.SECRET_KEY = "%032x" % random.getrandbits(128)
    if not 'INTERFACEOPTIONS' in settingkeys:
        settings.INTERFACEOPTIONS = ""
    if not 'CUSTOMHTML_INDEX' in settingkeys:
        if os.path.exists(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_index.html'):
            with io.open(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_index.html','r',encoding='utf-8') as f:
                settings.CUSTOMHTML_INDEX = f.read()
        else:
            settings.CUSTOMHTML_INDEX = ""
    if not 'CUSTOMHTML_PROJECTSTART' in settingkeys:
        if os.path.exists(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectstart.html'):
            with io.open(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectstart.html','r',encoding='utf-8') as f:
                settings.CUSTOMHTML_PROJECTSTART = f.read()
        else:
            settings.CUSTOMHTML_PROJECTSTART = ""
    if not 'CUSTOMHTML_PROJECTDONE' in settingkeys:
        if os.path.exists(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectstart.html'):
            with io.open(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectstart.html','r',encoding='utf-8') as f:
                settings.CUSTOMHTML_PROJECTDONE = f.read()
        else:
            settings.CUSTOMHTML_PROJECTDONE = ""

    if not 'CUSTOM_FORMATS' in settingkeys:
        settings.CUSTOM_FORMATS = []
    clam.common.data.CUSTOM_FORMATS = settings.CUSTOM_FORMATS #dependency injection

    if not 'ACTIONS' in settingkeys:
        settings.ACTIONS = []

    if not 'SESSIONDIR' in settingkeys:
        settings.SESSIONDIR = settings.ROOT + 'sessions'



def test_dirs():
    if not os.path.isdir(settings.ROOT):
        warning("Root directory does not exist yet, creating...")
        os.makedirs(settings.ROOT)
    if not os.path.isdir(settings.ROOT + 'projects'):
        warning("Projects directory does not exist yet, creating...")
        os.makedirs(settings.ROOT + 'projects')
    else:
        if not os.path.isdir(settings.ROOT + 'projects/anonymous'):
            warning("Directory for anonymous user not detected, migrating existing project directory from CLAM <0.7 to >=0.7")
            os.makedirs(settings.ROOT + 'projects/anonymous')
            for d in glob.glob(settings.ROOT + 'projects/*'):
                if os.path.isdir(d) and os.path.basename(d) != 'anonymous':
                    if d[-1] == '/': d = d[:-1]
                    warning("\tMoving " + d + " to " + settings.ROOT + 'projects/anonymous/' + os.path.basename(d))
                    shutil.move(d, settings.ROOT + 'projects/anonymous/' + os.path.basename(d))

    if not os.path.isdir(settings.SESSIONDIR):
        warning("Session directory does not exist yet, creating...")
        os.makedirs(settings.SESSIONDIR)
        
    if not settings.PARAMETERS:
            warning("No parameters specified in settings module!")
    if not settings.USERS and not settings.USERS_MYSQL and not settings.PREAUTHHEADER and not settings.OAUTH:
            warning("No user authentication enabled, this is not recommended for production environments!")
    if settings.OAUTH:
        if not settings.OAUTH_CLIENT_ID:
            error("ERROR: OAUTH enabled but OAUTH_CLIENT_ID not specified!")
        if not settings.OAUTH_CLIENT_SECRET:
            error("ERROR: OAUTH enabled but OAUTH_CLIENT_SECRET not specified!")
        if not settings.OAUTH_AUTH_URL:
            error("ERROR: OAUTH enabled but OAUTH_AUTH_URL not specified!")
        if not settings.OAUTH_TOKEN_URL:
            error("ERROR: OAUTH enabled but OAUTH_TOKEN_URL not specified!")
        if not settings.OAUTH_USERNAME_FUNCTION:
            error("ERROR: OAUTH enabled but OAUTH_USERNAME_FUNCTION not specified!")
        if not settings.OAUTH_ENCRYPTIONSECRET:
            error("ERROR: OAUTH enabled but OAUTH_ENCRYPTIONSECRET not specified!")

        warning("*** OAUTH is enabled, make sure you are running CLAM through HTTPS or security is void! ***")


def test_version():
    global VERSION
    #Check version
    req = str(settings.REQUIRE_VERSION).split('.')
    ver = str(VERSION).split('.')

    uptodate = True
    for i in range(0,len(req)):
        if i < len(ver):
            if req[i] > ver[i]:
                uptodate = False
                break
            elif ver[i] > req[i]:
                break
    if not uptodate:
        error("Version mismatch: at least " + str(settings.REQUIRE_VERSION) + " is required")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    settingsmodule = None
    fastcgi = False
    PORT = HOST = FORCEURL = None
    PYTHONPATH = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdH:p:vu:P:")
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-d':
            DEBUG = True
            setdebug(True)
        elif o == '-H':
            HOST = a
        elif o == '-p':
            PORT = int(a)
        elif o == '-P':
            PYTHONPATH = a
        elif o == '-h':
            usage()
            sys.exit(0)
        elif o == '-u':
            FORCEURL = a
        elif o == '-v':
            print("CLAM WebService version " + str(VERSION))
            sys.exit(0)
        else:
            usage()
            print("ERROR: Unknown option: ", o,file=sys.stderr)
            sys.exit(2)

    if (len(args) == 1):
        settingsmodule = args[0]
    elif (len(args) > 1):
        print("ERROR: Too many arguments specified",file=sys.stderr)
        usage()
        sys.exit(2)
    else:
        print("ERROR: No settings module specified!",file=sys.stderr)
        usage()
        sys.exit(2)





    if PYTHONPATH:
        sys.path.append(PYTHONPATH)

    import_string = "import " + settingsmodule + " as settings"
    exec(import_string)

    try:
        if settings.DEBUG:
            DEBUG = True
            setdebug(True)
    except:
        pass
    try:
        if settings.LOGFILE:
            setlogfile(settings.LOGFILE)
    except:
        pass

    test_version()
    if HOST:
        settings.HOST = HOST
    set_defaults()
    test_dirs()

    if FORCEURL:
        settings.FORCEURL = FORCEURL
    if PORT:
        settings.PORT = PORT

    if settings.URLPREFIX:
        settings.STANDALONEURLPREFIX = settings.URLPREFIX
        warning("WARNING: Using URLPREFIX in standalone mode! Are you sure this is what you want?")
        #raise Exception("Can't use URLPREFIX when running in standalone mode!")
    settings.URLPREFIX = '' #standalone server always runs at the root

    try:
        CLAMService('debug' if DEBUG else 'standalone') #start
    except socket.error:
        error("Unable to open socket. Is another service already running on this port?")

def run_wsgi(settings_module):
    """Run CLAM in WSGI mode"""
    global settingsmodule, DEBUG
    printdebug("Initialising WSGI service")

    globals()['settings'] = settings_module
    settingsmodule = settings_module.__name__

    try:
        if settings.DEBUG:
            DEBUG = True
            setdebug(True)
    except:
        pass

    test_version()
    if DEBUG:
        setlog(sys.stderr)
    else:
        setlog(None)
    try:
        if settings.LOGFILE:
            setlogfile(settings.LOGFILE)
    except:
        pass
    set_defaults() #host, port
    test_dirs()

    if DEBUG:
        from werkzeug.debug import DebuggedApplication
        return DebuggedApplication(CLAMService('wsgi').service.wsgi_app, True)
    else:
        return CLAMService('wsgi').service.wsgi_app
