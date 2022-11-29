#!/usr/bin/env python3
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Webservice --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#
#       Centre for Language and Speech Technology, Radboud University Nijmegen
#       & KNAW Humanities Cluster
#
#       Licensed under GPLv3
#
###############################################################

#pylint: disable=redefined-builtin,trailing-whitespace,superfluous-parens,bad-classmethod-argument,wrong-import-order,wrong-import-position,ungrouped-imports

import shutil
import os
import io
import stat
import subprocess
import importlib
import glob
import sys
import datetime
import random
import re
import hashlib
import argparse
import time
import socket
import json
import mimetypes
import flask
import werkzeug
import requests
import base64
import copy

import clam.common.status
import clam.common.parameters
import clam.common.formats
import clam.common.auth
import clam.common.oauth
import clam.common.data
import clam.common.viewers
from clam.common.util import globsymlinks, setdebug, setlog, setlogfile, printlog, printdebug, xmlescape, withheaders, computediskusage, parse_accept_header
import clam.config.defaults as settings #will be overridden by real settings later
settings.INTERNALURLPREFIX = ''

from urllib.parse import urlencode, unquote

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


VERSION = clam.common.data.VERSION

DEBUG = False

DATEMATCH = re.compile(r'^[\d\.\-\s:]*$')

settingsmodule = None #will be overwritten later

setlog(sys.stderr)

HOST = PORT = None



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

def userdb_lookup_file(user, **authsettings):
    printdebug("Looking up user " + user)
    with open(settings.USERS_FILE,'r',encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line and line[0] != '#':
                fields = line.split("\t")
                if len(fields) != 2:
                    warning(f"Error in line {i+1} in password file, expected two columns")
                elif fields[0] == user:
                    return fields[1]
    raise KeyError(f"User {user} not in database") 

def userdb_lookup_mysql(user, **authsettings):
    printdebug("Looking up user " + user + " in MySQL")
    host,port, mysqluser,passwd, database, table, userfield, passwordfield, accesslist, denylist = validate_users_mysql()  #pylint: disable=unused-variable
    if denylist and user in denylist:
        printdebug("User in denylist")
        raise KeyError
    if accesslist and not (user in accesslist):
        printdebug("User not in accesslist")
        raise KeyError
    if isinstance(passwd,bytes): passwd = str(passwd,'utf-8')
    db = MySQLdb.connect(host=host,user=mysqluser,passwd=passwd,db=database, charset='utf8', use_unicode=True)
    cursor = db.cursor()
    #simple protection against sql injection
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
    #pylint: disable=unsupported-membership-test,unsubscriptable-object
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
        oauthsession = OAuth2Session(settings.OAUTH_CLIENT_ID, redirect_uri=os.path.join(settings.OAUTH_CLIENT_URL,"login"), scope=settings.OAUTH_SCOPE)
        if 'error' in flask.request.values:
            error = flask.request.values['error']
            try:
                error_msg = flask.request.values['error_message']
            except KeyError:
                error_msg = ""
            if error:
                printdebug("OAuth Login: Error from remote authorization provider: " + error + ": " + error_msg)
                return withheaders(flask.make_response("Error from remote authorization provider: " + error + ": " + error_msg,403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})

        try:
            code = flask.request.values['code']
        except KeyError:
            printdebug("OAuth Login: No code passed")
            return withheaders(flask.make_response('No code passed',403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
        try:
            state = flask.request.values['state']
        except KeyError:
            printdebug("OAuth Login: No state passed")
            return withheaders(flask.make_response('No state passed',403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})

        printdebug("OAuth Login: Fetching token")
        d = oauthsession.fetch_token(settings.OAUTH_TOKEN_URL, client_secret=settings.OAUTH_CLIENT_SECRET,authorization_response=os.path.join(settings.OAUTH_CLIENT_URL, 'login?code='+ code + '&state=' + state ))
        if not 'access_token' in d:
            printdebug("OAuth Login: Error fetching token")
            return withheaders(flask.make_response('No access token received from authorization provider',403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})

        #pylint: disable=bad-continuation
        printdebug("OAuth Login: Done")
        return withheaders(flask.make_response(flask.render_template('login.xml',
                        version=VERSION,
                        system_id=settings.SYSTEM_ID,
                        system_name=settings.SYSTEM_NAME,
                        system_description=settings.SYSTEM_DESCRIPTION,
                        system_author=settings.SYSTEM_AUTHOR,
                        system_affiliation=settings.SYSTEM_AFFILIATION,
                        system_version=settings.SYSTEM_VERSION,
                        system_email=settings.SYSTEM_EMAIL,
                        system_url=settings.SYSTEM_URL,
                        system_parent_url=settings.SYSTEM_PARENT_URL,
                        system_register_url=settings.SYSTEM_REGISTER_URL,
                        system_login_url=settings.SYSTEM_LOGIN_URL,
                        system_logout_url=settings.SYSTEM_LOGOUT_URL,
                        system_cover_url=settings.SYSTEM_COVER_URL,
                        system_license=settings.SYSTEM_LICENSE,
                        auth_type=auth_type(),
                        url=getrooturl(),
                        oauth_access_token=oauth_encrypt(d['access_token']))),
                   headers={'allow-origin': settings.ALLOW_ORIGIN}, cookies={'oauth_access_token': oauth_encrypt(d['access_token'])} )

def oauth_encrypt(oauth_access_token):
    #encrypt is a misnomer because we don't actually encrypt anything anymore!
    if not oauth_access_token:
        return "" #no oauth
    else:
        return oauth_access_token

class Logout(object):

    @staticmethod
    def GET(credentials = None):
        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
        if not settings.OAUTH:
            return withheaders(flask.make_response("You will be properly logged out only after closing your browser session",403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN, 'Clear-Site-Data': '"cache", "cookies", "storage", "executionContexts"' })
        elif not settings.OAUTH_REVOKE_URL:
            return withheaders(flask.make_response("Logged you out locally (however, no key revocation mechanism was defined at the remote end)",403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN, 'Clear-Site-Data': '"cache", "cookies", "storage", "executionContexts"' })
        else:
            response = requests.get(settings.OAUTH_REVOKE_URL + '/', data={'token': oauth_access_token })

            if response.status_code >= 200 and response.status_code < 300:
                return withheaders(flask.make_response("Logout successful, have a nice day",200),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN, 'Clear-Site-Data': '"cache", "cookies", "storage", "executionContexts"' })
            else:
                return withheaders(flask.make_response("Logout failed at remote end: we recommend to clear your browsing history and cache instead, especially if you are on a public computer",403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN, 'Clear-Site-Data': '"cache", "cookies", "storage", "executionContexts"' })

        return withheaders(flask.make_response("Logout successful, have a nice day",200),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN, 'Clear-Site-Data': '"cache", "cookies", "storage", "executionContexts"' })



def parsecredentials(credentials, verbose=False):
    oauth_access_token = ""
    _401response = None

    if settings.OAUTH and isinstance(credentials, tuple):
        oauth_access_token = credentials[1]
        user = credentials[0]
    elif isinstance(credentials, dict):
        if 'user' in credentials:
            user = credentials['user']
        if 'oauth_access_token' in credentials:
            oauth_access_token = credentials['oauth_access_token']
        if '401response' in credentials:
            _401response = credentials['401response']
    elif credentials:
        if isinstance(credentials, tuple):
            user = credentials[0]
        else:
            user = credentials
    else:
        user = 'anonymous'

    if '/' in user or user == '.' or user == '..' or len(user) > 200:
        return withheaders(flask.make_response("Username invalid",403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
    if verbose:
        authtype = "none"
        if settings.OAUTH:
            authtype = "oauth"
        elif settings.USERS or settings.USERS_MYSQL or settings.USERS_FILE:
            if settings.BASICAUTH and settings.DIGESTAUTH:
                authtype = "multi"
            elif settings.BASICAUTH:
                authtype = "basic"
            elif settings.DIGESTAUTH:
                authtype = "digest"
        return {'user': user, 'oauth_access_token': oauth_access_token, '401response': _401response, 'type': authtype}
    else:
        return user, oauth_access_token


def auth_type():
    types = []
    if settings.OAUTH:
        types.append("oauth")
    if settings.PREAUTHHEADER:
        types.append("preauth")
    if (settings.ASSUMESSL or settings.BASICAUTH) and (settings.USERS or settings.USERS_MYSQL or settings.USERS_FILE):
        types.append("basic")
    elif settings.USERS or settings.USERS_MYSQL or settings.USERS_FILE:
        types.append("digest")
    if types:
        return ",".join(types)
    else:
        return "none"


################# Views ##########################

#Are tied into flask later because at this point we don't have an app instance yet

def entryshortcut(credentials = None, fromstart=False): #pylint: disable=too-many-return-statements
    user, oauth_access_token = parsecredentials(credentials)
    rq = flask.request.values
    printdebug("Using entry shortcut")
    if 'project' in rq: #pylint: disable=too-many-nested-blocks
        if rq['project'].lower() in ('new','create'):
            projectprefix = rq['projectprefix'] if 'projectprefix' in rq else 'P'
            project = projectprefix + str("%034x" % random.getrandbits(128))
        else:
            project = rq['project']

        createresponse = Project.create(project,user)
        if createresponse is not None:
            #something went wrong during project creation
            return createresponse

        prefixes = []
        for profile in settings.PROFILES:
            for inputtemplate in profile.input:
                prefixes.append(inputtemplate.id+'_')
                data = {'filename':'', 'inputtemplate': inputtemplate.id}
                if inputtemplate.id + '_filename' in rq:
                    data['filename'] = rq[inputtemplate.id + '_filename']
                elif inputtemplate.filename:
                    data['filename'] = inputtemplate.filename
                elif inputtemplate.extension:
                    pass #should be handled by addfile automatically

                if inputtemplate.id in rq:
                    data['contents'] = rq[inputtemplate.id]
                elif inputtemplate.id + '_url' in rq:
                    data['url'] = unquote(rq[inputtemplate.id + '_url'])

                if ('url' in data or 'contents' in data):
                    #copy local parameters
                    for key, value in rq.items():
                        if key.startswith(inputtemplate.id + '_') and key not in (inputtemplate.id+'_filename',inputtemplate.id+'_url'):
                            data[key[len(inputtemplate.id+'_'):]] = value

                    addfileresult = addfile(project,data['filename'], user, data, None, 'true_on_success')
                    if addfileresult is not True:
                        return addfileresult


        if 'start' in rq and rq['start'].lower() in ('1','yes','true'):
            if not fromstart: #prevent endless recursion
                startresponse = Project.start(project, credentials)
                if startresponse.status_code != 202:
                    return startresponse
            else:
                return True #signals start to do a redirect itself after starting (otherwise GET parameters stick on subsequent reloads)

        #forward any unhandled parameters (issue #66)
        forward_rq = []
        for key, value in rq.items():
            if key not in ('project','start'):
                if not any( key.startswith(prefix) for prefix in prefixes):
                    forward_rq.append((key,value))

        return withheaders(flask.redirect(getrooturl() + '/' + project + ('/?' if forward_rq else '') + urlencode(forward_rq)),headers={'allow_origin': settings.ALLOW_ORIGIN})

    return None

def getprojects(user):
    projects = []
    totalsize = 0.0
    path = settings.ROOT + "projects/" + user
    if os.path.exists(os.path.join(path,'.index')):
        with io.open(os.path.join(path,'.index'),'r',encoding='utf-8') as f:
            try:
                data = json.load(f)
            except ValueError:
                printlog("Invalid json in .index")
                os.unlink(os.path.join(path,'.index'))
                return getprojects(user)
            totalsize = float(data['totalsize'])
            projects = data['projects']
    else:
        printdebug("Computing index for " + user + "...")
        for f in glob.glob(path + '/*'):
            if os.path.isdir(f):
                d = datetime.datetime.fromtimestamp(os.stat(f)[8])
                project = os.path.basename(f)
                projectsize, filecount = Project.getdiskusage(user,project )
                totalsize += projectsize
                projects.append( ( project , d.strftime("%Y-%m-%d %H:%M:%S"), round(projectsize,2), Project.simplestatus(project,user)  ) )
        printdebug("Writing index for " + user + "...")
        if os.path.exists(path):
            with io.open(os.path.join(path,'.index'),'w',encoding='utf-8') as f_index:
                json.dump({'totalsize': totalsize, 'projects': projects},f_index, ensure_ascii=False)
    return projects, round(totalsize)



def mainentry(credentials = None):
    """This is the main (root) entry point, it can direct to various pages based on configuration and authentication"""

    user, oauth_access_token = parsecredentials(credentials)

    #handle shortcut
    shortcutresponse = entryshortcut((user,oauth_access_token))
    if shortcutresponse is not None:
        return shortcutresponse

    #when JSON(-LD) response is requested, just return the info page
    accept = parse_accept_header(flask.request)
    if accept and 'application/ld+json' in accept[0] or 'application/json' in accept[0]:
        return info(credentials)

    if user == "anonymous" and auth_type() != "none" and not settings.DISABLE_PORCH:
        #present an unauthenticated landing page without project index
        return porch(credentials)
    else:
        #present the project index
        return index((user,oauth_access_token))


def index(credentials = None):
    """Get list of projects or shortcut to other functionality"""

    projects = []
    user, oauth_access_token = parsecredentials(credentials)
    totalsize = 0.0
    if settings.LISTPROJECTS:
        projects, totalsize = getprojects(user)

    errors = "no"
    errormsg = ""

    corpora = CLAMService.corpusindex()


    #pylint: disable=bad-continuation
    return withheaders(flask.make_response(flask.render_template('response.xml',
            version=VERSION,
            system_id=settings.SYSTEM_ID,
            system_name=settings.SYSTEM_NAME,
            system_description=settings.SYSTEM_DESCRIPTION,
            system_author=settings.SYSTEM_AUTHOR,
            system_affiliation=settings.SYSTEM_AFFILIATION,
            system_version=settings.SYSTEM_VERSION,
            system_email=settings.SYSTEM_EMAIL,
            system_url=settings.SYSTEM_URL,
            system_parent_url=settings.SYSTEM_PARENT_URL,
            system_register_url=settings.SYSTEM_REGISTER_URL,
            system_login_url=settings.SYSTEM_LOGIN_URL,
            system_logout_url=settings.SYSTEM_LOGOUT_URL,
            system_cover_url=settings.SYSTEM_COVER_URL,
            system_license=settings.SYSTEM_LICENSE,
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
            formats=clam.common.data.getformats(settings.PROFILES),
            datafile=None,
            projects=projects,
            totalsize=totalsize,
            actions=settings.ACTIONS,
            disableinterface=not settings.ENABLEWEBAPP,
            info=False,
            porch=False,
            #mergexsl=flask.request.user_agent.browser in ("chrome","safari"),
            accesstoken=None,
            interfaceoptions=settings.INTERFACEOPTIONS,
            customhtml=settings.CUSTOMHTML_INDEX,
            customcss=settings.CUSTOMCSS,
            allow_origin=settings.ALLOW_ORIGIN,
            oauth_access_token=oauth_encrypt(oauth_access_token),
            auth_type=auth_type()
            )), headers={'allow_origin':settings.ALLOW_ORIGIN}) #pylint: disable=bad-continuation


def porch(credentials=None):
    """Public landing page, provides some info about the system without authentication"""
    projects = []
    user, oauth_access_token = parsecredentials(credentials)

    errors = "no"
    errormsg = ""

    #pylint: disable=bad-continuation
    return withheaders(flask.make_response(flask.render_template('response.xml',
            version=VERSION,
            system_id=settings.SYSTEM_ID,
            system_name=settings.SYSTEM_NAME,
            system_description=settings.SYSTEM_DESCRIPTION,
            system_author=settings.SYSTEM_AUTHOR,
            system_affiliation=settings.SYSTEM_AFFILIATION,
            system_version=settings.SYSTEM_VERSION,
            system_email=settings.SYSTEM_EMAIL,
            system_url=settings.SYSTEM_URL,
            system_parent_url=settings.SYSTEM_PARENT_URL,
            system_register_url=settings.SYSTEM_REGISTER_URL,
            system_login_url=settings.SYSTEM_LOGIN_URL,
            system_logout_url=settings.SYSTEM_LOGOUT_URL,
            system_cover_url=settings.SYSTEM_COVER_URL,
            system_license=settings.SYSTEM_LICENSE,
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
            inputsources=[],
            outputpaths=None,
            inputpaths=None,
            profiles=settings.PROFILES,
            formats=clam.common.data.getformats(settings.PROFILES),
            datafile=None,
            projects=projects,
            actions=settings.ACTIONS,
            info=False,
            porch=True,
            disableinterface=not settings.ENABLEWEBAPP,
            #mergexsl=flask.request.user_agent.browser in ("chrome","safari"),
            accesstoken=None,
            interfaceoptions=settings.INTERFACEOPTIONS,
            customhtml=settings.CUSTOMHTML_INDEX,
            customcss=settings.CUSTOMCSS,
            allow_origin=settings.ALLOW_ORIGIN,
            oauth_access_token=oauth_encrypt(oauth_access_token),
            auth_type=auth_type()
    )), headers={'allow_origin': settings.ALLOW_ORIGIN})

def info(credentials=None):
    """Get info"""
    projects = []
    user, oauth_access_token = parsecredentials(credentials)

    totalsize = 0.0
    if settings.LISTPROJECTS:
        projects, totalsize = getprojects(user)

    errors = "no"
    errormsg = ""

    corpora = CLAMService.corpusindex()

    accept = parse_accept_header(flask.request)
    if accept and 'application/ld+json' in accept[0] or 'application/json' in accept[0] or flask.request.args.get("json") == "1":
        #pylint: disable=bad-continuation
        return withheaders(flask.make_response(flask.render_template('response.json',
                version=VERSION,
                system_id=settings.SYSTEM_ID,
                system_name=settings.SYSTEM_NAME,
                system_description=settings.SYSTEM_DESCRIPTION,
                system_author=settings.SYSTEM_AUTHOR,
                system_affiliation=settings.SYSTEM_AFFILIATION,
                system_version=settings.SYSTEM_VERSION,
                system_email=settings.SYSTEM_EMAIL,
                system_url=settings.SYSTEM_URL,
                system_parent_url=settings.SYSTEM_PARENT_URL,
                system_register_url=settings.SYSTEM_REGISTER_URL,
                system_login_url=settings.SYSTEM_LOGIN_URL,
                system_logout_url=settings.SYSTEM_LOGOUT_URL,
                system_cover_url=settings.SYSTEM_COVER_URL,
                system_license=settings.SYSTEM_LICENSE,
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
                formats=clam.common.data.getformats(settings.PROFILES),
                datafile=None,
                projects=projects,
                actions=settings.ACTIONS,
                info=True,
                porch=False,
                allow_origin=settings.ALLOW_ORIGIN,
                oauth_access_token=oauth_encrypt(oauth_access_token),
                auth_type=auth_type()
        )), contenttype="application/ld+json", headers={'allow_origin': settings.ALLOW_ORIGIN})


    #pylint: disable=bad-continuation
    return withheaders(flask.make_response(flask.render_template('response.xml',
            version=VERSION,
            system_id=settings.SYSTEM_ID,
            system_name=settings.SYSTEM_NAME,
            system_description=settings.SYSTEM_DESCRIPTION,
            system_author=settings.SYSTEM_AUTHOR,
            system_affiliation=settings.SYSTEM_AFFILIATION,
            system_version=settings.SYSTEM_VERSION,
            system_email=settings.SYSTEM_EMAIL,
            system_url=settings.SYSTEM_URL,
            system_parent_url=settings.SYSTEM_PARENT_URL,
            system_register_url=settings.SYSTEM_REGISTER_URL,
            system_login_url=settings.SYSTEM_LOGIN_URL,
            system_logout_url=settings.SYSTEM_LOGOUT_URL,
            system_cover_url=settings.SYSTEM_COVER_URL,
            system_license=settings.SYSTEM_LICENSE,
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
            formats=clam.common.data.getformats(settings.PROFILES),
            datafile=None,
            projects=projects,
            actions=settings.ACTIONS,
            info=True,
            porch=False,
            #mergexsl=flask.request.user_agent.browser in ("chrome","safari"),
            disableinterface=not settings.ENABLEWEBAPP,
            accesstoken=None,
            interfaceoptions=settings.INTERFACEOPTIONS,
            customhtml=settings.CUSTOMHTML_INDEX,
            customcss=settings.CUSTOMCSS,
            allow_origin=settings.ALLOW_ORIGIN,
            oauth_access_token=oauth_encrypt(oauth_access_token),
            auth_type=auth_type()
    )), headers={'allow_origin': settings.ALLOW_ORIGIN})

class Admin:
    @staticmethod
    def index(credentials=None):
        """Get list of projects"""
        user, oauth_access_token = parsecredentials(credentials)
        if not settings.ADMINS or user not in settings.ADMINS:
            return flask.make_response('You shall not pass!!! You are not an administrator!',403)

        usersprojects = {}
        totalsize = {}
        for f in glob.glob(settings.ROOT + "projects/*"):
            if os.path.isdir(f):
                u = os.path.basename(f)
                usersprojects[u], totalsize[u] = getprojects(u)
                usersprojects[u].sort()

        return withheaders(flask.make_response(flask.render_template('admin.html',
                version=VERSION,
                system_id=settings.SYSTEM_ID,
                system_name=settings.SYSTEM_NAME,
                system_description=settings.SYSTEM_DESCRIPTION,
                system_author=settings.SYSTEM_AUTHOR,
                system_affiliation=settings.SYSTEM_AFFILIATION,
                system_version=settings.SYSTEM_VERSION,
                system_email=settings.SYSTEM_EMAIL,
                system_url=settings.SYSTEM_URL,
                system_parent_url=settings.SYSTEM_PARENT_URL,
                system_register_url=settings.SYSTEM_REGISTER_URL,
                system_login_url=settings.SYSTEM_LOGIN_URL,
                system_logout_url=settings.SYSTEM_LOGOUT_URL,
                system_cover_url=settings.SYSTEM_COVER_URL,
                system_license=settings.SYSTEM_LICENSE,
                user=user,
                url=getrooturl(),
                usersprojects = sorted(usersprojects.items()),
                totalsize=totalsize,
                allow_origin=settings.ALLOW_ORIGIN,
                oauth_access_token=oauth_encrypt(oauth_access_token)
        )), "text/html; charset=UTF-8", {'allow_origin':settings.ALLOW_ORIGIN}) #pylint: disable=bad-continuation

    @staticmethod
    def handler(command, targetuser, project, credentials=None): #pylint: disable=too-many-return-statements
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
                    system_author=settings.SYSTEM_AUTHOR,
                    system_affiliation=settings.SYSTEM_AFFILIATION,
                    system_version=settings.SYSTEM_VERSION,
                    system_email=settings.SYSTEM_EMAIL,
                    system_url=settings.SYSTEM_URL,
                    system_parent_url=settings.SYSTEM_PARENT_URL,
                    system_register_url=settings.SYSTEM_REGISTER_URL,
                    system_login_url=settings.SYSTEM_LOGIN_URL,
                    system_logout_url=settings.SYSTEM_LOGOUT_URL,
                    system_cover_url=settings.SYSTEM_COVER_URL,
                    system_license=settings.SYSTEM_LICENSE,
                    user=targetuser,
                    project=project,
                    inputfiles=sorted(inputfiles),
                    outputfiles=sorted(outputfiles),
                    url=getrooturl(),
                    allow_origin=settings.ALLOW_ORIGIN,
                    oauth_access_token=oauth_encrypt(oauth_access_token)
            )), "text/html; charset=UTF-8", {'allow_origin':settings.ALLOW_ORIGIN}) #pylint: disable=bad-continuation
        elif command == 'abort':
            p = Project()
            if p.abort(project, targetuser):
                return withheaders(flask.make_response("Ok"),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
            else:
                return withheaders(flask.make_response('Failed',403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
        elif command == 'delete':
            d = Project.path(project, targetuser)
            if os.path.isdir(d):
                shutil.rmtree(d)
                return withheaders(flask.make_response("Ok"),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
            else:
                return withheaders(flask.make_response('Not Found',403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
        else:
            return withheaders(flask.make_response('No such command: ' + command,403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})

    @staticmethod
    def downloader(targetuser, project, type, filename, credentials=None):
        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
        if not settings.ADMINS or not user in settings.ADMINS:
            return flask.make_response('You shall not pass!!! You are not an administrator!',403)

        if type == 'input':
            try:
                outputfile = clam.common.data.CLAMInputFile(Project.path(project, targetuser), filename)
            except:
                raise flask.abort(404)
        elif type == 'output':
            try:
                outputfile = clam.common.data.CLAMOutputFile(Project.path(project, targetuser), filename) #pylint: disable=redefined-variable-type
            except:
                raise flask.abort(404)
        else:
            return withheaders(flask.make_response('Invalid type',403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})

        if outputfile.metadata:
            headers = dict(list(outputfile.metadata.httpheaders()))
            mimetype = outputfile.metadata.mimetype
        else:
            headers = {}
            mimetype = 'application/octet-stream'
        headers['allow_origin'] = settings.ALLOW_ORIGIN
        try:
            return withheaders(flask.Response( (line for line in outputfile) ), mimetype, headers )
        except UnicodeError:
            return withheaders(flask.make_response("Output file " + str(outputfile) + " is not in the expected encoding! Make sure encodings for output templates service configuration file are accurate.",500),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
        except FileNotFoundError:
            raise flask.abort(404)
        except IOError:
            raise flask.abort(404)





def getrooturl(): #not a view
    if settings.USE_FORWARDED_HOST and 'X-Forwarded-Host' in flask.request.headers:
        url = flask.request.headers['X-Forwarded-Host']
        if settings.URLPREFIX and settings.URLPREFIX != '/':
            if settings.URLPREFIX[0] != '/':
                url = os.path.join(url, settings.URLPREFIX)
            else:
                url = os.path.join(url, settings.URLPREFIX[1:])
        if url[-1] == '/': url = url[:-1]
        if settings.FORCEHTTPS:
            url = "https://" + url
        elif 'X-Forwarded-Proto' in flask.request.headers:
            url =  flask.request.headers['X-Forwarded-Proto'] + "://" +  url
        else:
            url = "http://" + url
        return url
    elif settings.FORCEURL:
        if settings.FORCEHTTPS:
            return settings.FORCEURL.replace("http://","https://")
        else:
            return settings.FORCEURL
    else:
        url = flask.request.host_url
        if settings.URLPREFIX and settings.URLPREFIX != '/':
            if settings.URLPREFIX[0] != '/':
                url = os.path.join(url, settings.URLPREFIX)
            else:
                url = os.path.join(url, settings.URLPREFIX[1:])
        if url[-1] == '/': url = url[:-1]
        if settings.FORCEHTTPS:
            return url.replace("http://","https://")
        else:
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
        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
        return settings.ROOT + "projects/" + user + '/' + project + "/"

    @staticmethod
    def getdiskusage(user, project):
        path = settings.ROOT + "projects/" + user + '/' + project + "/"
        size, count = computediskusage(path)
        with open(os.path.join(path,'.du'),'w') as f:
            f.write(str(size) + "\n")
            f.write(str(count))
        return size, count

    @staticmethod
    def create(project, credentials): #pylint: disable=too-many-return-statements
        """Create project skeleton if it does not already exist (static method)"""

        if not settings.COMMAND:
            return flask.make_response("Projects disabled, no command configured",404)

        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
        if not Project.validate(project):
            return withheaders(flask.make_response('Invalid project ID. Note that only alphanumerical characters are allowed.',403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
        printdebug("Checking if " + settings.ROOT + "projects/" + user + '/' + project + " exists")
        if not project:
            return withheaders(flask.make_response('No project name',403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
        if not os.path.isdir(settings.ROOT + "projects/" + user):
            printlog("Creating user directory '" + user + "'")
            os.makedirs(settings.ROOT + "projects/" + user)
            if not os.path.isdir(settings.ROOT + "projects/" + user): #verify:
                return withheaders(flask.make_response("Directory " + settings.ROOT + "projects/" + user + " could not be created succesfully",403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})


        #checking user quota
        if settings.USERQUOTA > 0:
            _, totalsize = getprojects(user)
            if totalsize > settings.USERQUOTA:
                printlog("User " + user + " exceeded quota, refusing to create new project...")
                return withheaders(flask.make_response("Unable to create new project because you are exceeding your disk quota (max " + str(settings.USERQUOTA) + " MB, you now use " + str(totalsize) + " MB). Please delete some projects and try again.",403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})

        if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project):
            printlog("Creating project '" + project + "'")
            os.makedirs(settings.ROOT + "projects/" + user + '/' + project)

        if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/input/'):
            os.makedirs(settings.ROOT + "projects/" + user + '/' + project + "/input")
            if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/input'):
                return withheaders(flask.make_response("Input directory " + settings.ROOT + "projects/" + user + '/' + project + "/input/  could not be created succesfully",403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
        if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/output/'):
            os.makedirs(settings.ROOT + "projects/" + user + '/' + project + "/output")
            if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/output'):
                return withheaders(flask.make_response("Output directory " + settings.ROOT + "projects/" + user + '/' + project + "/output/  could not be created succesfully",403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
        if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/tmp/'):
            os.makedirs(settings.ROOT + "projects/" + user + '/' + project + "/tmp")
            if not os.path.isdir(settings.ROOT + "projects/" + user + '/' + project + '/tmp'):
                return withheaders(flask.make_response("tmp directory " + settings.ROOT + "projects/" + user + '/' + project + "/tmp/  could not be created succesfully",403),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})

        #Add project to index cache file
        indexfile = os.path.join(settings.ROOT + "projects/" + user,'.index')
        if os.path.exists(indexfile):
            with open(os.path.join(indexfile),'r',encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if 'projects' in data:
                        for projectdata in data['projects']:
                            if projectdata[0] == project:
                                return None #all is well, project already in index, nothing to do
                    d = datetime.datetime.fromtimestamp(os.stat(settings.ROOT + "projects/" + user + '/' + project)[8])
                    projectdata = ( project , d.strftime("%Y-%m-%d %H:%M:%S"), 0.00, clam.common.status.READY )
                    data['projects'].append(projectdata)
                    with open(os.path.join(indexfile),'w',encoding='utf-8') as f:
                        json.dump(data,f, ensure_ascii=False)
                except ValueError:
                    #something went wrong, delete the entire index (will be recomputed)
                    os.unlink(os.path.join(indexfile))

        return None #checks rely on this

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
        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
        printdebug("Checking if project " + project + " exists for " + user)
        return os.path.isdir(Project.path(project, user))

    @staticmethod
    def statuslog(project, user):
        statuslog = []
        statusfile = Project.path(project,user) + ".status"
        totalcompletion = 0
        if os.path.isfile(statusfile): #pylint: disable=too-many-nested-blocks
            prevmsg = None
            with open(statusfile, 'r', encoding='utf-8') as f:
                for line in f: #pylint: disable=too-many-nested-blocks
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
                                        except ValueError:
                                            pass
                                else:
                                    message += " " + field

                        if message and (message != prevmsg):
                            #print "STATUSLOG: t=",timestamp,"c=",completion,"msg=" + message.strip()
                            statuslog.append( (message.strip(), timestamp, completion) )
                            prevmsg = message
            statuslog.reverse()
        return statuslog, totalcompletion

    @staticmethod
    def status(project, user):
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
    def simplestatus(project, user):
        if Project.done(project, user):
            return clam.common.status.DONE
        elif Project.running(project, user):
            return clam.common.status.RUNNING
        else:
            return clam.common.status.READY

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
    def outputindex(project, user, d = '', quick=False):
        prefix = Project.path(project, user) + 'output/'
        begintime = time.time()
        for f in glob.glob(prefix + d + "/*"):
            if os.path.basename(f)[0] != '.': #always skip all hidden files
                if os.path.isdir(f):
                    for result in Project.outputindex(project, user, f[len(prefix):], quick):
                        yield result
                else:
                    file = clam.common.data.CLAMOutputFile(Project.path(project,user), f[len(prefix):], loadmetadata=not quick)
                    file.attachviewers(settings.PROFILES) #attaches converters as well
                    yield file
                if not quick and time.time() - begintime >= settings.QUICKTIMEOUT:
                    printlog("Loading output index is taking too long, enabling quick mode")
                    quick = True

    @staticmethod
    def inputindexbytemplate(project, user, inputtemplate):
        """Retrieve sorted index for the specified input template"""
        index = [] #pylint: disable=redefined-outer-name
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
        index = [] #pylint: disable=redefined-outer-name
        prefix = Project.path(project, user) + 'output/'
        for linkf, f in globsymlinks(prefix + '.*.OUTPUTTEMPLATE.' + outputtemplate.id + '.*'):
            seq = int(linkf.split('.')[-1])
            index.append( (seq,f) )

        #yield CLAMFile objects in proper sequence
        for seq, f in sorted(index):
            yield seq, clam.common.data.CLAMOutputFile(Project.path(project, user), f[len(prefix):])



    #main view
    @staticmethod
    def response(user, project, parameters, errormsg = "", datafile = False, oauth_access_token="", matchedprofiles=None, program=None,http_code=200):
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

        #quick mode skips metadata loading and may be useful on very large projects
        quick = 'quick' in flask.request.values and str(flask.request.values['quick']) == "1"

        if statuscode == clam.common.status.DONE:
            outputpaths = list(Project.outputindex(project, user,'',quick=quick))
            if Project.exitstatus(project, user) != 0: #non-zero codes indicate errors!
                errors = "yes"
                errormsg = "An error occurred within the system. Please inspect the error log for details"
                printlog("Child process failed, exited with non zero-exit code.")
                customhtml = settings.CUSTOMHTML_PROJECTFAILED
            else:
                customhtml = settings.CUSTOMHTML_PROJECTDONE
        else:
            outputpaths = []


        for parametergroup, parameterlist in parameters: #pylint: disable=unused-variable
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
                system_version=settings.SYSTEM_VERSION,
                system_author=settings.SYSTEM_AUTHOR,
                system_affiliation=settings.SYSTEM_AFFILIATION,
                system_email=settings.SYSTEM_EMAIL,
                system_url=settings.SYSTEM_URL,
                system_parent_url=settings.SYSTEM_PARENT_URL,
                system_register_url=settings.SYSTEM_REGISTER_URL,
                system_login_url=settings.SYSTEM_LOGIN_URL,
                system_logout_url=settings.SYSTEM_LOGOUT_URL,
                system_cover_url=settings.SYSTEM_COVER_URL,
                system_license=settings.SYSTEM_LICENSE,
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
                formats=clam.common.data.getformats(settings.PROFILES),
                matchedprofiles=matchedprofiles, #comma-separated list of indices (str)
                program=program, #Program instance
                datafile=datafile,
                projects=[],
                actions=settings.ACTIONS,
                disableinterface=not settings.ENABLEWEBAPP,
                info=False,
                porch=False,
                #mergexsl=flask.request.user_agent.browser in ("chrome","safari"),
                accesstoken=Project.getaccesstoken(user,project),
                interfaceoptions=settings.INTERFACEOPTIONS,
                customhtml=customhtml,
                customcss=settings.CUSTOMCSS,
                forwarders=[ forwarder(project, getrooturl(), Project.path(project,user)) for forwarder in  settings.FORWARDERS ],
                allow_origin=settings.ALLOW_ORIGIN,
                oauth_access_token=oauth_encrypt(oauth_access_token),
                auth_type=auth_type()
        ),http_code), headers={'allow_origin':settings.ALLOW_ORIGIN})


    @staticmethod
    def getaccesstoken(user,project):
        #for fineuploader, not oauth
        h = hashlib.md5()
        clear = user+ ':' + settings.PRIVATEACCESSTOKEN + ':' + project
        if isinstance(clear,str):
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
            return withheaders(flask.make_response("Project " + project + " was not found for user " + user,404) ,"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})#404
        else:
            #if user and not Project.access(project, user) and not user in settings.ADMINS:
            #    return flask.make_response("Access denied to project " +  project + " for user " + user, 401) #401
            datafile = os.path.join(Project.path(project,credentials),'clam.xml')
            statuscode, statusmsg, statuslog, completion = Project.status(project, user) #pylint: disable=unused-variable
            if statuscode == clam.common.status.DONE and os.path.exists(datafile):
                f = io.open(datafile,'r',encoding='utf-8')
                xmldata = f.read(os.path.getsize(datafile))
                f.close()
                data = clam.common.data.CLAMData(xmldata, None,False, Project.path(project,credentials), loadmetadata=False)
                return Project.response(user, project, settings.PARAMETERS,"",False,oauth_access_token,','.join([str(x) for x in data.program.matchedprofiles]) if data.program else "", data.program) #200
            else:
                #HTTP request parameters may be used to pre-set global parameters when starting a project (issue #66)
                for parametergroup, parameterlist in settings.PARAMETERS: #pylint: disable=unused-variable
                    for parameter in parameterlist:
                        value = parameter.valuefrompostdata(flask.request.values)
                        if value is not None:
                            parameter.set(value)
                return Project.response(user, project, settings.PARAMETERS,"",False,oauth_access_token) #200


    @staticmethod
    def new(project, credentials=None):
        """Create an empty project"""
        user, oauth_access_token = parsecredentials(credentials)
        response = Project.create(project, user)
        if response is not None:
            return response
        msg = "Project " + project + " has been created for user " + user
        return flask.make_response(msg, 201, {'Location': getrooturl() + '/' + project + '/', 'Content-Type':'text/plain','Content-Length': len(msg),'Access-Control-Allow-Origin': settings.ALLOW_ORIGIN, 'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE', 'Access-Control-Allow-Headers': 'Authorization', 'Referrer-Policy': 'strict-origin-when-cross-origin'}) #HTTP CREATED

    @staticmethod
    def start(project, credentials=None): #pylint: disable=too-many-return-statements
        """Start execution"""

        #handle shortcut
        shortcutresponse = entryshortcut(credentials, True) #protected against endless recursion, will return None when no shortcut is found, True when one is found and starting should continue
        if shortcutresponse is not None and shortcutresponse is not True:
            return shortcutresponse

        user, oauth_access_token = parsecredentials(credentials)
        response = Project.create(project, user)
        if response is not None:
            return response
        #if user and not Project.access(project, user):
        #    return flask.make_response("Access denied to project " + project +  " for user " + user,401) #401

        statuscode, _, _, _  = Project.status(project, user)
        if statuscode != clam.common.status.READY:
            return withheaders(flask.redirect(getrooturl() + '/' + project),headers={'allow_origin': settings.ALLOW_ORIGIN})

        #Generate arguments based on POSTed parameters
        commandlineparams = []
        postdata = flask.request.values

        errors, parameters, commandlineparams = clam.common.data.processparameters(postdata, settings.PARAMETERS)

        sufresources, resmsg = sufficientresources(user, project)
        if not sufresources:
            printlog("*** NOT ENOUGH SYSTEM RESOURCES AVAILABLE: " + resmsg + " ***")
            return withheaders(flask.make_response("There are not enough system resources available to accommodate your request. " + resmsg + " .Please try again later.",503),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
        if not errors: #We don't even bother running the profiler if there are errors
            matchedprofiles, program = clam.common.data.profiler(settings.PROFILES, Project.path(project, user), parameters, settings.SYSTEM_ID, settings.SYSTEM_NAME, getrooturl(), printdebug)
            #converted matched profiles to a list of indices
            matchedprofiles_byindex = []
            for i, profile in enumerate(settings.PROFILES):
                if profile in matchedprofiles:
                    matchedprofiles_byindex.append(i)

        if errors:
            #There are parameter errors, return 403 response with errors marked
            printlog("There are parameter errors, not starting.")
            return Project.response(user, project, parameters,"",False,oauth_access_token, http_code=403)
        elif not matchedprofiles:
            printlog("No profiles matching, not starting.")
            return Project.response(user, project, parameters, "No profiles matching input and parameters, unable to start. Are you sure you added all necessary input files and set all necessary parameters?", False, oauth_access_token,http_code=403)
        else:
            #everything good, write clam.xml output file and start
            with io.open(Project.path(project, user) + "clam.xml",'wb') as f:
                f.write(Project.response(user, project, parameters, "",True, oauth_access_token, ",".join([str(x) for x in matchedprofiles_byindex]), program).data)



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
            cmd = cmd.replace('$TMPDIRECTORY',Project.path(project, user) + 'tmp/')
            cmd = cmd.replace('$STATUSFILE',Project.path(project, user) + '.status')
            cmd = cmd.replace('$DATAFILE',Project.path(project, user) + 'clam.xml')
            cmd = cmd.replace('$USERNAME',user if user else "anonymous")
            cmd = cmd.replace('$PROJECT',project) #alphanumberic only, shell-safe
            cmd = cmd.replace('$OAUTH_ACCESS_TOKEN',oauth_access_token)
            cmd = clam.common.data.escapeshelloperators(cmd)
            #everything should be shell-safe now
            cmd += " 2> " + Project.path(project, user) + "output/error.log" #add error output

            pythonpath = ''
            try:
                pythonpath = ':'.join(settings.DISPATCHER_PYTHONPATH)
            except AttributeError:
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
                with open(Project.path(project, user) + '.pid','w') as f: #will be handled by dispatcher!
                    f.write(str(pid))
                if shortcutresponse is True:
                    #redirect to project page to lose parameters in URL
                    return withheaders(flask.redirect(getrooturl() + '/' + project),headers={'allow_origin': settings.ALLOW_ORIGIN})
                else:
                    #normal response (202)
                    return Project.response(user, project, parameters,"",False,oauth_access_token,",".join([str(x) for x in matchedprofiles_byindex]), program,http_code=202) #returns 202 - Accepted
            else:
                return withheaders(flask.make_response("Unable to launch process",500),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})

    @staticmethod
    def delete(project, credentials=None):
        data = flask.request.values
        if 'abortonly' in data:
            abortonly = bool(data['abortonly'])
        else:
            abortonly = False
        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
        if not Project.exists(project, user):
            return withheaders(flask.make_response("No such project: " + project + " for user " + user,404),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
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
        indexfile = os.path.join(settings.ROOT + "projects/" + user,'.index')
        if os.path.exists(indexfile):
            #delete project from the index cache
            data = {}
            with open(os.path.join(indexfile),'r',encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except ValueError:
                    #delete the entire index
                    data = {'projects': []}
                    os.unlink(os.path.join(indexfile))
            totalsize = 0.0
            newdata = {
                'projects': [],
                'totalsize': 0.0,
            }
            for i, projectdata in enumerate(data['projects']):
                if projectdata[0] != project:
                    newdata['projects'].append(projectdata)
                    totalsize += projectdata[2]
            newdata['totalsize'] = totalsize
            with open(os.path.join(indexfile),'w',encoding='utf-8') as f:
                json.dump(newdata,f, ensure_ascii=False)

        return withheaders(flask.make_response(msg),'text/plain',{'Content-Length':len(msg), 'allow_origin': settings.ALLOW_ORIGIN})  #200


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
    def shareoutputfile(project, filename, credentials=None):
        """Put a file into temporary public storage"""
        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
        try:
            outputfile = clam.common.data.CLAMOutputFile(Project.path(project, user), filename)
            fileid = put_storage(outputfile)
        except FileNotFoundError:
            return withheaders(flask.make_response('File not found',404),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})

        return withheaders(flask.make_response(json.dumps({
            "id": fileid,
            "filename": filename,
            "url": getrooturl() + "/storage/" + fileid
        })),'application/json',{'allow_origin': settings.ALLOW_ORIGIN})

    @staticmethod
    def getoutputfile(project, filename, credentials=None): #pylint: disable=too-many-return-statements
        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
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
                    return withheaders(flask.make_response(outputfile.metadata.xml()) ,  headers={'allow_origin': settings.ALLOW_ORIGIN})
                else:
                    return withheaders(flask.make_response("No metadata found!",404),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
            elif requestid in ('share','shareonce') and settings.ALLOWSHARE:
                viewer = clam.common.viewers.ShareViewer(id="share",more=True,persistent=(requestid=='share'))
                output = viewer.view(outputfile, baseurl=getrooturl())
                if isinstance(output, (flask.Response, werkzeug.wrappers.Response)):
                    return output
                else:
                    return withheaders(flask.Response(  (line for line in output ) , 200), viewer.mimetype,  headers={'allow_origin': settings.ALLOW_ORIGIN}) #streaming output
            else:
                #attach viewer data (also attaches converters!)
                outputfile.attachviewers(settings.PROFILES)

                #set remote properties, used by the ForwardViewer
                outputfile.baseurl = getrooturl()
                outputfile.project = project
                outputfile.user = user

                viewer = None
                for v in outputfile.viewers:
                    if v.id == requestid:
                        viewer = v
                if viewer:
                    kwargs = {}
                    kwargs.update(flask.request.values)
                    kwargs['path'] = Project.path(project, user)
                    viewer.baseurl = getrooturl()
                    output = viewer.view(outputfile, **kwargs)
                    if isinstance(output, (flask.Response, werkzeug.wrappers.Response)):
                        return output
                    else:
                        return withheaders(flask.Response(  (line for line in output ) , 200), viewer.mimetype,  headers={'allow_origin': settings.ALLOW_ORIGIN}) #streaming output
                else:
                    #Check for converters
                    for c in outputfile.converters:
                        if c.id == requestid:
                            converter = c
                    if converter:
                        return withheaders( flask.Response( ( line for line in converter.convertforoutput(outputfile) ),200), headers={'allow_origin': settings.ALLOW_ORIGIN}  )
                    else:
                        return withheaders(flask.make_response("No such viewer or converter:" + requestid,404),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
        elif not requestarchive:
            #normal request - return file contents

            #pro-actively check if file exists
            if not os.path.exists(str(outputfile)):
                raise flask.abort(404)

            if outputfile.metadata:
                printdebug("Obtaining headers for " + outputfile.metadata.__class__.__name__)
                headers = dict(list(outputfile.metadata.httpheaders()))
                mimetype = outputfile.metadata.mimetype
            else:
                printdebug("No metadata found for output file " + str(outputfile))
                headers = {}
                if os.path.basename(str(outputfile)) in ('log','error.log'):
                    mimetype = 'text/plain'
                else:
                    #guess mimetype
                    mimetype = mimetypes.guess_type(str(outputfile))[0]
                if not mimetype: mimetype = 'application/octet-stream'
            headers['allow_origin'] = settings.ALLOW_ORIGIN
            printdebug("Returning output file " + str(outputfile) + " with mimetype " + mimetype + " and headers: " + repr(headers))
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

        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
        if filename: filename = filename.replace("..","") #Simple security

        if not filename or len(filename) == 0:
            #Deleting all output files and resetting
            Project.reset(project, user)
            msg = "Deleted"
            return withheaders(flask.make_response(msg), 'text/plain',{'Content-Length':len(msg), 'allow_origin': settings.ALLOW_ORIGIN}) #200
        elif os.path.isdir(Project.path(project, user) + filename):
            #Deleting specified directory
            shutil.rmtree(Project.path(project, user) + filename)
            msg = "Deleted"
            return withheaders(flask.make_response(msg), 'text/plain',{'Content-Length':len(msg), 'allow_origin': settings.ALLOW_ORIGIN}) #200
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
                return withheaders(flask.make_response(msg), 'text/plain',{'Content-Length':len(msg), 'allow_origin': settings.ALLOW_ORIGIN}) #200


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
        """Generates and returns a download package (or 403 if one is already in the process of being prepared, though this does function blocks until the package is ready)"""
        if os.path.isfile(Project.path(project, user) + '.download'):
            #make sure we don't start two compression processes at the same time
            return withheaders(flask.make_response('Another compression is already running',403),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
        else:
            contentencoding = None
            if not format:
                data = flask.request.values
                if 'format' in data:
                    format = data['format']
                else:
                    format = 'zip' #default

            try:
                printlog("Requested download archive in " + format + " format")
                archivefile, contenttype, contentencoding = clam.common.data.buildarchive(project, Project.path(project,user), format)
            except ValueError:
                return withheaders(flask.make_response('Invalid archive format',403) ,"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
            except RuntimeError as e:
                return withheaders(flask.make_response("Unable to make download package: " + str(e),500),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})

            extraheaders = {
                'allow_origin': settings.ALLOW_ORIGIN,
                'Content-Disposition': 'attachment; filename="' + project +  '.' + format + '"'
            }
            if contentencoding:
                extraheaders['Content-Encoding'] = contentencoding
            return withheaders(flask.Response( getbinarydata(archivefile) ), contenttype, extraheaders )


    @staticmethod
    def getinputfile(project, filename, credentials=None):
        requestid = None
        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable

        raw = filename.split('/')

        if filename.strip('/') == "":
            #this is a request for the index
            return withheaders(flask.make_response("Permission denied",403),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
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
                    return withheaders(flask.make_response(inputfile.metadata.xml()), headers={'allow_origin': settings.ALLOW_ORIGIN})
                else:
                    return withheaders(flask.make_response("No metadata found!",404),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
            else:
                raise flask.abort(404)
        else:
            #normal request - return file contents

            #pro-actively check if file exists
            if not os.path.exists(str(inputfile)):
                raise flask.abort(404)

            if inputfile.metadata:
                headers = dict(list(inputfile.metadata.httpheaders()))
                mimetype = inputfile.metadata.mimetype
            else:
                printdebug("No metadata found for input file " + str(inputfile))
                headers = {}
                mimetype = mimetypes.guess_type(str(inputfile))[0]
                if not mimetype: mimetype = 'application/octet-stream'
            headers['allow_origin'] = settings.ALLOW_ORIGIN
            try:
                printdebug("Returning input file " + str(inputfile) + " with mimetype " + mimetype)
                return withheaders(flask.Response( (line for line in inputfile) ), mimetype, headers )
            except UnicodeError:
                return withheaders(flask.make_response("Input file " + str(inputfile) + " is not in the expected encoding! Make sure encodings for output templates service configuration file are accurate.",500),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
            except FileNotFoundError:
                raise flask.abort(404)
            except IOError:
                raise flask.abort(404)

    @staticmethod
    def deleteinputfile(project, filename, credentials=None):
        """Delete an input file"""

        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
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
                return withheaders(flask.make_response(msg),'text/plain', {'Content-Length': len(msg), 'allow_origin': settings.ALLOW_ORIGIN}) #200

    @staticmethod
    def addinputfile_nofile(project, credentials=None):
        printdebug('Addinputfile_nofile' )
        return Project.addinputfile(project,'',credentials)

    @staticmethod
    def addinputfile(project, filename, credentials=None): #pylint: disable=too-many-return-statements
        """Add a new input file, this invokes the actual uploader"""

        printdebug('Addinputfile: Initialising' )

        user, oauth_access_token = parsecredentials(credentials) #pylint: disable=unused-variable
        response = Project.create(project, user)
        if response is not None:
            return response
        postdata = flask.request.values

        if Project.simplestatus(project, user) != clam.common.status.READY:
            return withheaders(flask.make_response("No input files accepted at this stage",403),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})

        if filename == '': #pylint: disable=too-many-nested-blocks
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
                    return withheaders(flask.make_response("No such inputsource exists",403),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
                if not inputtemplate:
                    for profile in settings.PROFILES:
                        for t in profile.input:
                            if inputsource.inputtemplate == t.id:
                                inputtemplate = t
                if inputtemplate is None:
                    return withheaders(flask.make_response("No input template found for inputsource",500),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
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
                return withheaders(flask.make_response("No filename or inputsource specified",403),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
        else:
            #Simply forward to addfile
            return addfile(project,filename,user, postdata)



def addfile(project, filename, user, postdata, inputsource=None,returntype='xml'): #pylint: disable=too-many-return-statements
    """Add a new input file, this invokes the actual uploader"""


    def errorresponse(msg, code=403, xml=""):
        if returntype == 'json':
            return withheaders(flask.make_response(json.dumps({
                "success": False,
                "error": msg,
                "xml": xml,
            })),'application/json',{'allow_origin': settings.ALLOW_ORIGIN})
        else:
            if not xml:
                return withheaders(flask.make_response(msg,403),'text/plain',headers={'allow_origin': settings.ALLOW_ORIGIN})
            else:
                #ignore msg, send only xml
                return withheaders(flask.make_response(xml,403),headers={'allow_origin': settings.ALLOW_ORIGIN})

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
            return withheaders(flask.make_response("Specified inputtemplate (" + inputtemplate_id + ") not found!",404),headers={'allow_origin': settings.ALLOW_ORIGIN})
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
            return errorresponse("No inputtemplate specified nor auto-detected for filename " + filename + "!",404)



    #See if other previously uploaded input files use this inputtemplate
    if inputtemplate.unique:
        nextseq = 0 #unique
    else:
        nextseq = 1 #will hold the next sequence number for this inputtemplate (in multi-mode only)

    for seq, inputfile in Project.inputindexbytemplate(project, user, inputtemplate): #pylint: disable=unused-variable
        if inputtemplate.unique:
            return errorresponse("You have already submitted a file of this type, you can only submit one. Delete it first. (Inputtemplate=" + inputtemplate.id + ", unique=True)")
        else:
            if seq >= nextseq:
                nextseq = seq + 1 #next available sequence number


    if not filename: #Actually, I don't think this can occur at this stage, but we'll leave it in to be sure (yes it can, when the entry shortcut is used!)
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
                if not filename[:-len(inputtemplate.extension) - 1]:
                    #file name is only an extension! add random component
                    filename = "input-" + str("%x" % random.getrandbits(64)) + filename
                filename = filename[:-len(inputtemplate.extension) - 1] +  '.' + inputtemplate.extension
            else:
                if not filename:
                    #no file name specified, add a random component
                    filename = "input-" + str("%x" % random.getrandbits(64))
                filename = filename +  '.' + inputtemplate.extension
                #return flask.make_response("Specified filename does not have the extension dictated by the inputtemplate ("+inputtemplate.extension+")") #403

    if inputtemplate.onlyinputsource and (not 'inputsource' in postdata or not postdata['inputsource']):
        return errorresponse("Adding files for this inputtemplate must proceed through inputsource")

    if 'converter' in postdata and postdata['converter'] and not postdata['converter'] in [ x.id for x in inputtemplate.converters]:
        return errorresponse("Invalid converter specified: " + postdata['converter'])

    #Make sure the filename is secure
    validfilename = True
    DISALLOWED = ('/','&','|','<','>',';','"',"'","`","{","}","\n","\r","\b","\t")
    for c in filename:
        if c in DISALLOWED:
            validfilename = False
            break

    if not validfilename:
        return errorresponse("Filename contains invalid symbols! Do not use /,&,|,<,>,',`,\",{,} or ;")


    #Create the project (no effect if already exists)
    response = Project.create(project, user)
    if response is not None:
        return response


    printdebug("(Obtaining filename for uploaded file)")
    head = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
    head += "<clamupload>\n"
    if 'file' in flask.request.files:
        printlog("Adding client-side file " + flask.request.files['file'].filename + " to input files")
        sourcefile = flask.request.files['file'].filename
    elif 'url' in postdata and postdata['url']:
        #Download from URL
        postdata['url'] = unquote(postdata['url'])
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
                return errorresponse("Specified inputsource '" + postdata['inputsource'] + "' does not exist for inputtemplate '"+inputtemplate.id+"'")
        sourcefile = os.path.basename(inputsource.path)
    elif 'accesstoken' in postdata and 'filename' in postdata:
        #XHR POST, data in body
        printlog("Adding client-side file " + filename + " to input files. Uploaded using XHR POST")
        sourcefile = postdata['filename']
    else:
        return errorresponse("No file, url or contents specified!")


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
        except Exception as e: #pylint: disable=broad-except
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
        except: #pylint: disable=bare-except
            printlog("Uploaded metadata is invalid!")
            metadata = None
            errors = True
            parameters = []
            validmeta = False
    elif 'inputsource' in postdata and postdata['inputsource']:
        printlog("Getting metadata from inputsource, uploading...")
        if inputsource.metadata:
            printlog("Validating metadata from inputsource")
            metadata = inputsource.metadata
            errors, parameters = inputtemplate.validate(metadata, user)
            validmeta = True
        else:
            printlog("No metadata provided with inputsource, looking for metadata files..")
            metafilename = os.path.dirname(inputsource.path)
            if metafilename: metafilename += '/'
            metafilename += '.' + os.path.basename(inputsource.path) + '.METADATA'
            if os.path.exists(metafilename):
                try:
                    metadata = clam.common.data.CLAMMetaData.fromxml(open(metafilename,'r').readlines())
                    errors, parameters = inputtemplate.validate(metadata, user)
                    validmeta = True
                except: #pylint: disable=bare-except
                    printlog("Uploaded metadata is invalid!")
                    metadata = None
                    errors = True
                    parameters = []
                    validmeta = False
            else:
                return withheaders(flask.make_response("No metadata found nor specified for inputsource " + inputsource.id ,500),headers={'allow_origin': settings.ALLOW_ORIGIN})
    else:
        errors, parameters = inputtemplate.validate(postdata, user)
        validmeta = True #will be checked later


    #  ----------- Check if archive are allowed -------------
    archive = False
    addedfiles = []
    if not errors and inputtemplate.acceptarchive: #pylint: disable=too-many-nested-blocks
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
                with open(Project.path(project,user) + archive,'wb') as f:
                    while True:
                        chunk = flask.request.stream.read(16384)
                        if chunk:
                            f.write(chunk)
                        else:
                            break
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
            except: #pylint: disable=bare-except
                return withheaders(flask.make_response("Unable to extract archive",500),headers={'allow_origin': settings.ALLOW_ORIGIN})
            out, _ = process.communicate() #waits for process to end

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
    for filename in addedfiles: #pylint: disable=too-many-nested-blocks
        output += "<upload source=\""+sourcefile +"\" filename=\""+filename+"\" inputtemplate=\"" + inputtemplate.id + "\" templatelabel=\""+inputtemplate.label+"\" format=\""+inputtemplate.formatclass.__name__+"\">\n"
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
                    postdata['url'] = unquote(postdata['url'])
                    printdebug('(Receiving data from url: ' + postdata['url'] + " )" )
                    #Download file from 3rd party server to CLAM server
                    try:
                        r = requests.get(postdata['url'])
                    except:
                        return withheaders(flask.make_response("No remote data could be obtained from " + postdata['url'],404),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
                    if not (r.status_code >= 200 and r.status_code < 300):
                        return withheaders(flask.make_response("No remote data could be obtained from " + postdata['url'] + ". Server returned HTTP " + str(r.status_code),404),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})

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
                        return errorresponse("Input file " + str(filename) + " is not in the expected encoding!")
                elif 'accesstoken' in postdata and 'filename' in postdata:
                    printdebug('(Receiving data directly from post body)')
                    with open(Project.path(project,user) + 'input/' + filename,'wb') as f:
                        while True:
                            chunk = flask.request.stream.read(16384)
                            if chunk:
                                f.write(chunk)
                            else:
                                break

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
                    elif 'validation_error' in metadata:
                        metadataerror = metadata['validation_error']
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

            if 'validation_error' in metadata:
                printdebug('(Metadata could not be generated, ' + str(metadataerror) + ') due to validation error')
                jsonoutput['error'] = fatalerror = "Input not accepted (validation failed): " + str(metadataerror)
                output += "<error>" + xmlescape(fatalerror) + "</error>"
                jsonoutput['success'] = False
                #remove upload
                os.unlink(Project.path(project, user) + 'input/' + filename)
            elif metadataerror:
                printdebug('(Metadata could not be generated, ' + str(metadataerror) + ',  this usually indicated an error in service configuration)')
                jsonoutput['error'] = fatalerror = "Metadata could not be generated! " + str(metadataerror) + "  (this usually indicates an error in service configuration!)"
                output += "<error>" + xmlescape(fatalerror) + "</error>"
                jsonoutput['success'] = False
                #remove upload
                os.unlink(Project.path(project, user) + 'input/' + filename)
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
                        except: #pylint: disable=bare-except
                            success = False
                        if not success:
                            conversionerror = True
                            jsonoutput['error'] = fatalerror = "Unable to convert"
                            output += "<error>" + xmlescape(fatalerror) + "</error>"
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
                        jsonoutput['error'] = fatalerror = "The file did not validate, it is not in the proper expected format."
                        jsonoutput['success'] = False
                        output += "<error>" + xmlescape(fatalerror) + "</error>"
                        #remove upload
                        os.unlink(Project.path(project, user) + 'input/' + filename)


        output += "</upload>\n"

    output += "</clamupload>"



    if returntype == 'boolean':
        return jsonoutput['success']
    elif fatalerror:
        #fatal error return error message with 403 code
        printlog('Fatal Error during upload: ' + fatalerror)
        return errorresponse(fatalerror,403, output)
    elif errors:
        #parameter errors, return XML output with 403 code
        printdebug('There were parameter errors during upload!')
        if returntype == 'json':
            jsonoutput['xml'] = output #embed XML in JSON for complete client-side processing
            return withheaders(flask.make_response(json.dumps(jsonoutput)), 'application/json', {'allow_origin': settings.ALLOW_ORIGIN})
        else:
            return withheaders(flask.make_response(output,403),headers={'allow_origin': settings.ALLOW_ORIGIN})
    elif returntype == 'xml': #success
        printdebug('Returning xml')
        return withheaders(flask.make_response(output), 'text/xml', {'allow_origin': settings.ALLOW_ORIGIN})
    elif returntype == 'json': #success
        printdebug('Returning json')
        #everything ok, return JSON output (caller decides)
        jsonoutput['xml'] = output #embed XML in JSON for complete client-side processing
        return withheaders(flask.make_response(json.dumps(jsonoutput)), 'application/json', {'allow_origin': settings.ALLOW_ORIGIN})
    elif returntype == 'true_on_success':
        return True
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

    return withheaders(flask.make_response("systemid = '"+ settings.SYSTEM_ID + "'; baseurl = '" + getrooturl() + "';\n inputtemplates = [ " + ",".join(inputtemplates) + " ];"), 'text/javascript', {'allow_origin': settings.ALLOW_ORIGIN})

def foliaxsl(**kwargs):
    if foliatools is not None:
        return withheaders(flask.make_response(io.open(foliatools.__path__[0] + '/folia2html.xsl','r',encoding='utf-8').read()),'text/xsl', {'allow_origin': settings.ALLOW_ORIGIN})
    else:
        return withheaders(flask.make_response("folia.xsl is not available, no FoLiA Tools installed on this server",404),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})


def styledata():
    if settings.STYLE[0] == '/':
        return withheaders(flask.make_response(io.open(settings.STYLE,'r',encoding='utf-8').read()),'text/css', {'allow_origin': settings.ALLOW_ORIGIN})
    else:
        return withheaders(flask.make_response(io.open(settings.CLAMDIR + '/style/' + settings.STYLE + '.css','r',encoding='utf-8').read()),'text/css', {'allow_origin': settings.ALLOW_ORIGIN})


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
        return withheaders(flask.make_response("{success: false, error: 'No accesstoken given'}"),'application/json', {'allow_origin': settings.ALLOW_ORIGIN})
    if accesstoken != Project.getaccesstoken(user,project):
        return withheaders(flask.make_response("{success: false, error: 'Invalid accesstoken given'}"),'application/json', {'allow_origin': settings.ALLOW_ORIGIN})
    if not os.path.exists(Project.path(project, user)):
        return withheaders(flask.make_response("{success: false, error: 'Destination does not exist'}"),'application/json', {'allow_origin': settings.ALLOW_ORIGIN})
    else:
        return addfile(project,filename,user, postdata,None, 'json' )


def get_storage(fileid):
    """Get a file from temporary public storage"""

    if not fileid or not all( c.isdigit() or c in ('a','b','c','d','e','f') for c in fileid ):
        return withheaders(flask.make_response("Malformed file id",403),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
    printdebug("Getting file from public storage " + fileid)
    storagedir = settings.ROOT + "storage/" + fileid
    if os.path.exists(storagedir):
        buildarchivetrigger = os.path.join(storagedir,".buildarchive")
        if os.path.exists(buildarchivetrigger):
            #the archive has not actually been built yet, we trigger a build now
            with open(buildarchivetrigger,'r',encoding='utf-8') as f:
                project, path, archivetype = f.readline().split("\t")
            os.unlink(buildarchivetrigger)
            archivefile, _, _ = clam.common.data.buildarchive(project, path, archivetype)
            archivefile = clam.common.data.CLAMOutputFile(path, project + "." + archivetype, False)
            archivefile.store(fileid)
            outputfile = archivefile
        else:
            try:
                filename = [ f for f in glob.glob(storagedir + "/*") if f[0] != '.' ][0]
            except IndexError:
                return withheaders(flask.make_response("No file found for given id",404),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})

            try:
                outputfile = clam.common.data.CLAMFile(os.path.dirname(filename), os.path.basename(filename))
            except:
                return withheaders(flask.make_response("Unable to load file",403),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})

        if outputfile.metadata:
            headers = dict(list(outputfile.metadata.httpheaders()))
            mimetype = outputfile.metadata.mimetype
        else:
            headers = {}
            mimetype = 'application/octet-stream'
        headers['allow_origin'] = settings.ALLOW_ORIGIN
        headers['Content-Disposition'] = "attachment; filename=\"" + outputfile.filename + "\""

        if not outputfile.exists():
            return withheaders(flask.make_response("File not found: " + str(outputfile),404),'text/plain', {'allow_origin': settings.ALLOW_ORIGIN})

        try:
            response = withheaders(flask.Response( outputfile.readlines() ), mimetype, headers ) #warning: loads output into memory! needed because we will delete the file afterward
        except UnicodeError:
            return withheaders(flask.make_response("Output file " + str(outputfile) + " is not in the expected encoding! Make sure encodings for output templates service configuration file are accurate.",500),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})

        if not os.path.exists(os.path.join(storagedir, ".keep")) and ('keep' not in flask.request.values or flask.request.values['keep'] in ('0','no','false')):
            printdebug("Removing storage " + fileid)
            shutil.rmtree(storagedir)

        return response

    else:
        return withheaders(flask.make_response("No such file id",404),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})

def put_storage(file):
    """Put a file in temporary public storage, returns the ID"""
    assert isinstance(file, clam.common.data.CLAMFile)
    if not os.path.exists(str(file)):
        raise FileNotFoundError
    fileid = None
    while fileid is None or os.path.exists(settings.ROOT + "storage/" + fileid):
        fileid = str("%x" % random.getrandbits(128))
    printdebug("Putting file into public storage " + fileid)
    storagedir = settings.ROOT + "storage/" + fileid
    os.makedirs(storagedir)
    os.symlink(str(file), os.path.join(storagedir, file.filename))
    metafile = file.projectpath + file.basedir + '/' + file.metafilename()
    if os.path.exists(metafile):
        os.symlink(metafile, os.path.join(storagedir, file.metafilename()))
    return fileid


class ActionHandler:

    @staticmethod
    def find_action( actionid, method=None):
        for action in settings.ACTIONS:
            if action.id == actionid and (not action.method or not method or method == action.method):
                return action
        raise Exception("No such action: " + actionid)

    @staticmethod
    def collect_parameters(action):
        params = []
        for parameter in action.parameters:
            if not parameter.id in flask.request.args and not parameter.id in flask.request.form:
                if parameter.required:
                    raise clam.common.data.ParameterError("Missing parameter: " + parameter.id)
            else:
                if parameter.id in flask.request.args:
                    paramvalue = flask.request.args[parameter.id]
                elif parameter.id in flask.request.form:
                    paramvalue = flask.request.form[parameter.id]
                if parameter.paramflag:
                    flag = parameter.paramflag
                else:
                    flag = None
                parameter = copy.deepcopy(parameter) #always operate on a COPY of the parameter
                if not parameter.set(paramvalue):
                    raise clam.common.data.ParameterError("Invalid value for parameter " + parameter.id + ": " + parameter.error)
                else:
                    params.append( ( flag, parameter.value, parameter.id) )
        return params


    @staticmethod
    def do( actionid, method, user="anonymous", oauth_access_token=""): #pylint: disable=too-many-return-statements
        try:
            printdebug("Looking for action " + actionid)
            action = ActionHandler.find_action(actionid, method)
        except:
            return withheaders(flask.make_response("Action does not exist",404),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})

        printdebug("Performing action " + action.id + " (user=" + user +")")

        viewer = None

        userdir =  settings.ROOT + "projects/" + user + '/'

        if action.command: #pylint: disable=too-many-nested-blocks
            cmd = action.command

            parameters = ""
            try:
                collectedparams =ActionHandler.collect_parameters(action)
            except clam.common.data.ParameterError as e:
                return withheaders(flask.make_response(str(e),403),headers={'allow_origin': settings.ALLOW_ORIGIN})

            for flag, value, paramid in collectedparams:
                if not isinstance(value, str):
                    value = str(value)
                if value:
                    try:
                        if cmd.find('$' + paramid + '$') != -1:
                            cmd = cmd.replace('$' + paramid + '$', clam.common.data.shellsafe(value,'"'))
                        else:
                            if parameters: parameters += " "
                            if flag: parameters += flag + " "
                            parameters += clam.common.data.shellsafe(value,'"')
                    except ValueError as e:
                        return withheaders(flask.make_response("Parameter " + paramid + " has an invalid value...",403),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
                if paramid == "viewer" and value:
                    try:
                        viewer = [ v for v in action.viewers if v.id == value ][0]
                    except IndexError:
                        return withheaders(flask.make_response("Requested viewer not found!", 404), "text/plain", {'allow_origin': settings.ALLOW_ORIGIN})

            if action.tmpdir is True or cmd.find('$TMPDIRECTORY') != -1:
                tmpdir = os.path.join(settings.SESSIONDIR, 'atmp.' + str("%034x" % random.getrandbits(128)))
                passdir = 'tmp://' + tmpdir
                passcwd = tmpdir
            elif action.tmpdir:
                tmpdir = action.tmpdir
                passcwd = tmpdir
                passdir = 'tmp://' + tmpdir
            else:
                tmpdir = None
                passdir = 'NONE'
                if os.path.exists(userdir):
                    passcwd = userdir
                elif 'TMPDIR' in os.environ and os.path.exists(os.environ['TMPDIR']):
                    #fallback, not user-specific!
                    passcwd = os.environ['TMPDIR']
                else:
                    #fallback, not user-specific!
                    passcwd = "/tmp"

            if tmpdir:
                try:
                    os.mkdir(tmpdir)
                except: #pylint: disable=bare-except
                    return withheaders(flask.make_response("Unable to create temporary action directory",500),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})

            cmd = cmd.replace('$PARAMETERS', parameters)
            if tmpdir:
                cmd = cmd.replace('$TMPDIRECTORY', tmpdir)
            cmd = cmd.replace('$USERNAME',user if user else "anonymous")
            cmd = cmd.replace('$OAUTH_ACCESS_TOKEN',oauth_access_token if oauth_access_token else "")
            cmd = clam.common.data.escapeshelloperators(cmd)
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

            cmd = settings.DISPATCHER + ' ' + pythonpath + ' ' + settingsmodule + ' ' + passdir + ' ' + cmd
            if settings.REMOTEHOST:
                if settings.REMOTEUSER:
                    cmd = "ssh -o NumberOfPasswordPrompts=0 " + settings.REMOTEUSER + "@" + settings.REMOTEHOST + " " + cmd
                else:
                    cmd = "ssh -o NumberOfPasswordPrompts=0 " + settings.REMOTEHOST + " " + cmd
            printlog("Starting dispatcher " +  settings.DISPATCHER + " for action " + actionid + " with " + action.command + ": " + repr(cmd) + " ..." )
            process = subprocess.Popen(cmd,cwd=passcwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process:
                printlog("Waiting for dispatcher (pid " + str(process.pid) + ") to finish" )
                stdoutdata, stderrdata = process.communicate()
                stdoutdata = str(stdoutdata,'utf-8')
                stderrdata = str(stderrdata,'utf-8')
                if DEBUG:
                    printdebug("    action stdout:\n" + stdoutdata)
                    printdebug("    action stderr:\n" + stderrdata)
                printlog("Dispatcher finished with code " + str(process.returncode) )
                if tmpdir:
                    shutil.rmtree(tmpdir)
                if process.returncode in action.returncodes200:
                    if viewer:
                        output = viewer.view(io.StringIO(stdoutdata), baseurl=getrooturl())
                        if isinstance(output, (flask.Response, werkzeug.wrappers.Response)):
                            return output
                        else:
                            return withheaders(flask.Response(  (line for line in output ) , 200), viewer.mimetype,  headers={'allow_origin': settings.ALLOW_ORIGIN}) #streaming output
                    else:
                        #normal response without a viewer
                        return withheaders(flask.make_response(stdoutdata,200),action.mimetype, {'allow_origin': settings.ALLOW_ORIGIN}) #200
                elif process.returncode in action.returncodes403:
                    return withheaders(flask.make_response(stdoutdata,403), action.mimetype, {'allow_origin': settings.ALLOW_ORIGIN})
                elif process.returncode in action.returncodes404:
                    return withheaders(flask.make_response(stdoutdata, 404), action.mimetype, {'allow_origin': settings.ALLOW_ORIGIN})
                else:
                    return withheaders(flask.make_response("Process for action " +  actionid + " failed\n" + stderrdata,500),"text/plain",headers={'allow_origin': settings.ALLOW_ORIGIN})
            else:
                return withheaders(flask.make_response("Unable to launch process",500),"text/plain", headers={'allow_origin': settings.ALLOW_ORIGIN})
        elif action.function:
            args = []
            kwargs = {}
            for _, value, paramid in ActionHandler.collect_parameters(action):
                if paramid != 'viewer':
                    args.append(value)
                    kwargs[paramid] = value
                else:
                    if value:
                        try:
                            viewer = [ v for v in action.viewers if v.id == str(value) ][0]
                        except IndexError:
                            return withheaders(flask.make_response("Requested viewer not found!", 404), "text/plain", {'allow_origin': settings.ALLOW_ORIGIN})

            try:
                if action.parameterstyle == 'keywords':
                    result = action.function(**kwargs)
                else:
                    result = action.function(*args)
            except Exception as e: #pylint: disable=broad-except
                if isinstance(e, werkzeug.exceptions.HTTPException):
                    raise
                else:
                    return withheaders(flask.make_response(e,500),headers={'allow_origin': settings.ALLOW_ORIGIN})
            if not isinstance(result, (flask.Response, werkzeug.wrappers.Response)):
                if viewer:
                    output = viewer.view(io.StringIO(str(result)), baseurl=getrooturl())
                    return withheaders(flask.Response(  (line for line in output ) , 200), viewer.mimetype,  headers={'allow_origin': settings.ALLOW_ORIGIN}) #streaming output
                else:
                    return withheaders(flask.make_response(str(result)), action.mimetype, {'allow_origin': settings.ALLOW_ORIGIN})
            else:
                return result
        else:
            raise Exception("No command or function defined for action " + actionid)

    @staticmethod
    def run(actionid, method, credentials=None):
        credentials = parsecredentials(credentials, verbose=True) #verbose returns a more verbose dictionary of credentials
        action = ActionHandler.find_action(actionid, method)
        if action.allowanonymous or credentials['user'] != 'anonymous' or credentials['type'] == "none":
            return ActionHandler.do(actionid, method,credentials['user'],credentials['oauth_access_token'] if 'oauth_access_token' in credentials else "")
        elif '401response' in credentials and credentials['401response'] is not None:
            #we are anonymous but this action does not allow that:
            printdebug("(anonymous access not allowed, returning deferred 401 response)")
            return credentials['401response']
        else:
            #we are anonymous but this action does not allow that:
            printdebug("(anonymous access not allowed, crafting dummy 401 response)")
            res = flask.make_response("Authorization required")
            res.status_code = 401
            return res

    @staticmethod
    def GET(actionid, credentials=None):
        return ActionHandler.run(actionid, 'GET', credentials)

    @staticmethod
    def POST(actionid, credentials=None):
        return ActionHandler.run(actionid, 'POST', credentials)

    @staticmethod
    def PUT(actionid, credentials=None):
        return ActionHandler.run(actionid, 'PUT', credentials)

    @staticmethod
    def DELETE(actionid, credentials=None):
        return ActionHandler.run(actionid, 'DELETE', credentials)


def sufficientresources(user, project):
    if not settings.ENABLED:
        return False, "Service is disabled for maintenance"
    if settings.REQUIREMEMORY > 0:
        if not os.path.exists('/proc/meminfo'):
            printlog("WARNING: No /proc/meminfo available on your system! Not Linux? Skipping memory requirement check!")
        else:
            memavail = cached = 0.0
            with open('/proc/meminfo') as f:
                for line in f:
                    if line[0:13] == "MemAvailable:":
                        memavail = float(line[14:].replace('kB','').strip()) #in kB
                    if line[0:7] == "Cached:":
                        cached = float(line[14:].replace('kB','').strip()) #in kB
            if settings.REQUIREMEMORY * 1024 > memavail + cached:
                return False, str(settings.REQUIREMEMORY * 1024) + " kB memory is required but only " + str(memavail + cached) + " is available."
    if settings.MAXLOADAVG > 0:
        if not os.path.exists('/proc/loadavg'):
            printlog("WARNING: No /proc/loadavg available on your system! Not Linux? Skipping load average check!")
        else:
            with open('/proc/loadavg') as f:
                line = f.readline()
                loadavg = float(line.split(' ')[0])
            if settings.MAXLOADAVG < loadavg:
                return False, "System load too high: " + str(loadavg) + ", max is " + str(settings.MAXLOADAVG)
    if settings.MINDISKSPACE and settings.DISK:
        dffile = '/tmp/df.' + str("%034x" % random.getrandbits(128))
        ret = os.system('df -mP ' + settings.DISK + " | gawk '{ print $4; }'  > " + dffile)
        if ret == 0:
            try:
                with open(dffile,'r') as f:
                    free = int(f.readlines()[-1])
                if free < settings.MINDISKSPACE:
                    os.unlink(dffile)
                    return False, "Not enough diskspace, " + str(free) + " MB free, need at least " + str(settings.MINDISKSPACE) + " MB"
            except:
                printlog("WARNING: df " + settings.DISK + " failed (unexpected format). Skipping disk space check!")
                os.unlink(dffile)

        else:
            printlog("WARNING: df " + settings.DISK + " failed. Skipping disk space check!")
    if user:
        projects, totalsize = getprojects(user)
        if settings.USERQUOTA > 0 and totalsize > settings.USERQUOTA:
            return False , "You exceeded your disk quota, refusing to start the project"
        if settings.MAXCONCURRENTPROJECTSPERUSER > 0:
            running = 0
            for p in projects:
                if p[3] == clam.common.status.RUNNING:
                    running += 1
            if running >= settings.MAXCONCURRENTPROJECTSPERUSER:
                return False , "You may only run " + str(settings.MAXCONCURRENTPROJECTSPERUSER) + " project(s) simultaneously and you are already at this maximum. Refusing to start the project."
        if settings.PROJECTQUOTA > 0 and project:
            for p in projects:
                if p[0] == project:
                    if p[2] > settings.PROJECTQUOTA:
                        return False, "Your project is too large, to run. The input files exceed the maximum of "  + str(settings.PROJECTQUOTA) + " MB. Refusing to start the project."
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
                        if isinstance(base, bytes):
                            base = str(base, 'utf-8')
                        interpreter = base + '/bin/python'
                    elif 'home' in uwsgi.opt and uwsgi.opt['home']:
                        base = uwsgi.opt['home']
                        if isinstance(base, bytes):
                            base = str(base, 'utf-8')
                        interpreter = uwsgi.opt['home'] + '/bin/python'
                    else:
                        interpreter = 'python3'
                else:
                    interpreter = sys.executable
                settings.COMMAND = interpreter + " " + settings.COMMAND
            else:
                error("Specified command " + settings.COMMAND.split(" ")[0] + " is not executable")
        else:
            lastparameter = None
            try:
                for parametergroup, parameters in settings.PARAMETERS: #pylint: disable=unused-variable
                    for parameter in parameters:
                        assert isinstance(parameter, clam.common.parameters.AbstractParameter)
                        lastparameter = parameter
            except AssertionError:
                msg = "Syntax error in parameter specification."
                if lastparameter:
                    msg += "Last part parameter: ", lastparameter.id
                error(msg)

        if settings.OAUTH:
            if not settings.ASSUMESSL: warning("*** Oauth Authentication is enabled. THIS IS NOT SECURE WITHOUT SSL! ***")
            main_auth = clam.common.auth.OAuth2(settings.OAUTH_CLIENT_ID, settings.OAUTH_AUTH_URL, os.path.join(settings.OAUTH_CLIENT_URL, 'login'), settings.OAUTH_AUTH_FUNCTION, settings.OAUTH_USERNAME_FUNCTION, debug=printdebug,scope=settings.OAUTH_SCOPE, userinfo_url=settings.OAUTH_USERINFO_URL)
            #Allow combinations with HTTP Basic Auth
            if settings.USERS:
                basic_auth = clam.common.auth.HTTPBasicAuth(get_password=userdb_lookup_dict, realm=settings.REALM,debug=printdebug)
                self.auth = clam.common.auth.MultiAuth(main_auth, basic_auth)
            elif settings.USERS_FILE:
                basic_auth = clam.common.auth.HTTPBasicAuth(get_password=userdb_lookup_file, realm=settings.REALM,debug=printdebug)
                self.auth = clam.common.auth.MultiAuth(main_auth, basic_auth)
            elif settings.USERS_MYSQL:
                validate_users_mysql()
                basic_auth = clam.common.auth.HTTPBasicAuth(get_password=userdb_lookup_mysql, realm=settings.REALM,debug=printdebug)
                self.auth = clam.common.auth.MultiAuth(main_auth, basic_auth)
            else:
                self.auth = main_auth
        elif settings.PREAUTHHEADER:
            warning("*** Forwarded Authentication is enabled. THIS IS NOT SECURE WITHOUT A PROPERLY CONFIGURED AUTHENTICATION PROVIDER! ***")
            self.auth = clam.common.auth.ForwardedAuth(settings.PREAUTHHEADER, debug=printdebug) #pylint: disable=redefined-variable-type
        elif settings.USERS:
            if settings.BASICAUTH:
                basic_auth = clam.common.auth.HTTPBasicAuth(get_password=userdb_lookup_dict, realm=settings.REALM,debug=printdebug)
                if not settings.ASSUMESSL: warning("*** HTTP Basic Authentication is enabled. THIS IS NOT SECURE WITHOUT SSL! ***")
            if settings.DIGESTAUTH:
                digest_auth = clam.common.auth.HTTPDigestAuth(settings.SESSIONDIR,get_password=userdb_lookup_dict, realm=settings.REALM,debug=printdebug) #pylint: disable=redefined-variable-type
            if settings.BASICAUTH and settings.DIGESTAUTH:
                self.auth = clam.common.auth.MultiAuth(basic_auth, digest_auth) #pylint: disable=redefined-variable-type
            elif settings.BASICAUTH:
                self.auth = basic_auth #pylint: disable=redefined-variable-type
            elif settings.DIGESTAUTH:
                self.auth = digest_auth
            else:
                error("USERS is set but no authentication mechanism is enabled, set BASICAUTH and/or DIGESTAUTH to True")
        elif settings.USERS_FILE:
            if settings.BASICAUTH:
                basic_auth = clam.common.auth.HTTPBasicAuth(get_password=userdb_lookup_file, realm=settings.REALM,debug=printdebug)
                if not settings.ASSUMESSL: warning("*** HTTP Basic Authentication is enabled. THIS IS NOT SECURE WITHOUT SSL! ***")
            if settings.DIGESTAUTH:
                digest_auth = clam.common.auth.HTTPDigestAuth(settings.SESSIONDIR,get_password=userdb_lookup_file, realm=settings.REALM,debug=printdebug) #pylint: disable=redefined-variable-type
            if settings.BASICAUTH and settings.DIGESTAUTH:
                self.auth = clam.common.auth.MultiAuth(basic_auth, digest_auth) #pylint: disable=redefined-variable-type
            elif settings.BASICAUTH:
                self.auth = basic_auth #pylint: disable=redefined-variable-type
            elif settings.DIGESTAUTH:
                self.auth = digest_auth
            else:
                error("USERS_FILE is set but no authentication mechanism is enabled, set BASICAUTH and/or DIGESTAUTH to True")
        elif settings.USERS_MYSQL:
            validate_users_mysql()
            if settings.BASICAUTH:
                basic_auth = clam.common.auth.HTTPBasicAuth(get_password=userdb_lookup_mysql, realm=settings.REALM,debug=printdebug)
                if not settings.ASSUMESSL: warning("*** HTTP Basic Authentication is enabled. THIS IS NOT SECURE WITHOUT SSL! ***")
            if settings.DIGESTAUTH:
                digest_auth = clam.common.auth.HTTPDigestAuth(settings.SESSIONDIR, get_password=userdb_lookup_mysql,realm=settings.REALM,debug=printdebug) #pylint: disable=redefined-variable-type
            if settings.BASICAUTH and settings.DIGESTAUTH:
                self.auth = clam.common.auth.MultiAuth(basic_auth, digest_auth) #pylint: disable=redefined-variable-type
            elif settings.BASICAUTH:
                self.auth = basic_auth #pylint: disable=redefined-variable-type
            elif settings.DIGESTAUTH:
                self.auth = digest_auth
            else:
                error("USERS is set but no authentication mechanism is enabled, set BASICAUTH and/or DIGESTAUTH to True")
        else:
            warning("*** NO AUTHENTICATION ENABLED!!! This is strongly discouraged in production environments! ***")
            self.auth = clam.common.auth.NoAuth() #pylint: disable=redefined-variable-type

        printdebug("Full settings dump: " + repr(vars(settings)))


        printdebug("Initialising flask service")
        self.service = flask.Flask("clam")
        self.service.jinja_env.trim_blocks = True
        self.service.jinja_env.lstrip_blocks = True
        self.service.secret_key = settings.SECRET_KEY
        printdebug("Registering main entrypoint: " + settings.INTERNALURLPREFIX + "/")
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/', '', self.auth.require_login(mainentry, optional=True), methods=['GET'] )

        #versions without trailing slash so no automatic 308 redirect is needed (which flask does by itself otherwise!)
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/index', 'index2', self.auth.require_login(index), methods=['GET'], strict_slashes=False )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/porch', 'porch2', porch, methods=['GET'], strict_slashes=False )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/info', 'info2', info, methods=['GET'], strict_slashes=False )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/login', 'login2', Login.GET, methods=['GET'] , strict_slashes=False)
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/logout', 'logout2', self.auth.require_login(Logout.GET), methods=['GET'], strict_slashes=False )

        #canonical versions
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/index/', 'index', self.auth.require_login(index), methods=['GET'], strict_slashes=False )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/porch/', 'porch', porch, methods=['GET'] , strict_slashes=False)
        printdebug("Registering info entrypoint: " + settings.INTERNALURLPREFIX + "/info/")
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/info/', 'info', info, methods=['GET'] , strict_slashes=False)
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/login/', 'login', Login.GET, methods=['GET'] , strict_slashes=False)
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/logout/', 'logout', self.auth.require_login(Logout.GET), methods=['GET'] , strict_slashes=False)


        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/storage/<fileid>', 'get_storage', get_storage, methods=['GET'] )

        #Authentication for handler is handled deeper in the ActionHandler, depending on whether allowanonymous is set
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/actions/<actionid>', 'action_get2', self.auth.require_login(ActionHandler.GET, optional=True), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/actions/<actionid>', 'action_post2', self.auth.require_login(ActionHandler.POST, optional=True), methods=['POST'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/actions/<actionid>', 'action_put2', self.auth.require_login(ActionHandler.PUT, optional=True), methods=['PUT'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/actions/<actionid>', 'action_delete2', self.auth.require_login(ActionHandler.DELETE, optional=True), methods=['DELETE'] )

        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/status', 'project_status_json2', Project.status_json, methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/upload', 'project_uploader2', uploader, methods=['POST'] ) #has it's own login mechanism
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>', 'project_get2', self.auth.require_login(Project.get), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>', 'project_start2', self.auth.require_login(Project.start), methods=['POST'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>', 'project_new2', self.auth.require_login(Project.new), methods=['PUT'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>', 'project_delete2', self.auth.require_login(Project.delete), methods=['DELETE'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/zip', 'project_download_zip2', self.auth.require_login(Project.download_zip), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/gz', 'project_download_targz2', self.auth.require_login(Project.download_targz), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/bz2', 'project_download_tarbz22', self.auth.require_login(Project.download_tarbz2), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output', 'project_download_zip3', self.auth.require_login(Project.download_zip), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/input', 'project_addinputfile3', self.auth.require_login(Project.addinputfile_nofile), methods=['POST','GET'] )

        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/data.js', 'interfacedata', interfacedata, methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/style.css', 'styledata', styledata, methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/admin/', 'adminindex', self.auth.require_login(Admin.index), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/admin/download/<targetuser>/<project>/<type>/<filename>/', 'admindownloader', self.auth.require_login(Admin.downloader), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/admin/<command>/<targetuser>/<project>/', 'adminhandler', self.auth.require_login(Admin.handler), methods=['GET'] )
        #Authentication for handler is handled deeper in the ActionHandler, depending on whether allowanonymous is set
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/actions/<actionid>/', 'action_get', self.auth.require_login(ActionHandler.GET, optional=True), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/actions/<actionid>/', 'action_post', self.auth.require_login(ActionHandler.POST, optional=True), methods=['POST'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/actions/<actionid>/', 'action_put', self.auth.require_login(ActionHandler.PUT, optional=True), methods=['PUT'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/actions/<actionid>/', 'action_delete', self.auth.require_login(ActionHandler.DELETE, optional=True), methods=['DELETE'] )

        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/zip/', 'project_download_zip', self.auth.require_login(Project.download_zip), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/gz/', 'project_download_targz', self.auth.require_login(Project.download_targz), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/bz2/', 'project_download_tarbz2', self.auth.require_login(Project.download_tarbz2), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/folia.xsl', 'foliaxsl', foliaxsl, methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/<path:filename>', 'project_getoutputfile', self.auth.require_login(Project.getoutputfile), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/<path:filename>', 'project_deleteoutputfile', self.auth.require_login(Project.deleteoutputfile), methods=['DELETE'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/<path:filename>', 'project_shareoutputfile', self.auth.require_login(Project.shareoutputfile), methods=['PUT'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/', 'project_download_zip4', self.auth.require_login(Project.download_zip), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/output/', 'project_deletealloutput', self.auth.require_login(Project.deletealloutput), methods=['DELETE'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/input/folia.xsl', 'input_foliaxsl', foliaxsl, methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/input/<path:filename>', 'project_getinputfile', self.auth.require_login(Project.getinputfile), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/input/<path:filename>', 'project_deleteinputfile', self.auth.require_login(Project.deleteinputfile), methods=['DELETE'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/input/<path:filename>', 'project_addinputfile', self.auth.require_login(Project.addinputfile), methods=['POST'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/input/', 'project_addinputfile2', self.auth.require_login(Project.addinputfile_nofile), methods=['POST','GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/status/', 'project_status_json', Project.status_json, methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/upload/', 'project_uploader', uploader, methods=['POST'] ) #has it's own login mechanism
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/', 'project_get', self.auth.require_login(Project.get), methods=['GET'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/', 'project_start', self.auth.require_login(Project.start), methods=['POST'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/', 'project_new', self.auth.require_login(Project.new), methods=['PUT'] )
        self.service.add_url_rule(settings.INTERNALURLPREFIX + '/<project>/', 'project_delete', self.auth.require_login(Project.delete), methods=['DELETE'] )


        self.mode = mode
        if self.mode != 'wsgi' and (settings.OAUTH or settings.PREAUTHHEADER or settings.BASICAUTH):
            warning("*** YOU ARE RUNNING THE DEVELOPMENT SERVER, THIS IS INSECURE WITH THE CONFIGURED AUTHENTICATION METHOD ***")
        if settings.PORT == 443:
            printlog("Server available on https://" + settings.HOST + '/' + settings.URLPREFIX)
        elif settings.PORT == 80:
            printlog("Server available on http://" + settings.HOST + '/' + settings.URLPREFIX)
        else:
            printlog("Server available on http://" + settings.HOST + ":" + str(settings.PORT) +'/' + settings.URLPREFIX)
        if settings.FORCEURL:
            printlog("Access using forced URL: " + settings.FORCEURL)

        if self.mode == 'wsgi':
            printdebug("DEBUG="+str(DEBUG))
            printdebug("CLAM started in wsgi mode")
            self.service.debug = DEBUG
        elif self.mode in ('standalone','debug'):
            self.service.debug = (mode == 'debug')
            printdebug("DEBUG="+str(mode=='debug'))
            printdebug("CLAM started in " + self.mode + " mode")
            self.service.run(host='0.0.0.0',port=settings.PORT)
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
    #Default settings
    settingkeys = dir(settings)

    if 'INTERNALURLPREFIX' not in settingkeys:
        settings.INTERNALURLPREFIX = ''

    for s in ['SYSTEM_ID','SYSTEM_DESCRIPTION','SYSTEM_NAME','ROOT','COMMAND','PROFILES']:
        if not s in settingkeys:
            error("ERROR: Service configuration incomplete, missing setting: " + s)

    if 'ROOT' in settingkeys and settings.ROOT and not settings.ROOT[-1] == "/":
        settings.ROOT += "/" #append slash
    clam.common.data.ROOT = settings.ROOT #dependency injection

    if 'SYSTEM_VERSION' not in settingkeys:
        settings.SYSTEM_VERSION = ""
    if 'SYSTEM_EMAIL' not in settingkeys:
        settings.SYSTEM_EMAIL = ""
    if 'SYSTEM_AUTHOR' not in settingkeys:
        settings.SYSTEM_AUTHOR = ""
    if 'SYSTEM_AFFILIATION' not in settingkeys:
        settings.SYSTEM_AFFILIATION = ""
    if 'SYSTEM_URL' not in settingkeys:
        settings.SYSTEM_URL = ""
    if 'SYSTEM_PARENT_URL' not in settingkeys:
        settings.SYSTEM_PARENT_URL = ""
    if 'SYSTEM_LOGIN_URL' not in settingkeys:
        settings.SYSTEM_LOGIN_URL = ""
    if 'SYSTEM_LOGOUT_URL' not in settingkeys:
        settings.SYSTEM_LOGOUT_URL = ""
    if 'SYSTEM_REGISTER_URL' not in settingkeys:
        settings.SYSTEM_REGISTER_URL = ""
    if 'SYSTEM_COVER_URL' not in settingkeys:
        settings.SYSTEM_COVER_URL = ""
    if 'SYSTEM_LICENSE' not in settingkeys:
        settings.SYSTEM_LICENSE = ""
    if 'USERS' not in settingkeys:
        settings.USERS = None
    if 'USERS_FILE' not in settingkeys:
        settings.USERS_FILE = None
    if 'ADMINS' not in settingkeys:
        settings.ADMINS = []
    if 'LISTPROJECTS' not in settingkeys:
        settings.LISTPROJECTS = True
    if 'ALLOWSHARE' not in settingkeys: #Allow sharing from the interface for all files
        settings.ALLOWSHARE = True
    if 'DISABLE_PORCH' not in settingkeys:
        settings.DISABLE_PORCH = False
    if 'PUBLIC_ACTIONS' not in settingkeys:
        settings.PUBLIC_ACTIONS = False
    if 'USERQUOTA' not in settingkeys:
        settings.USERQUOTA = 0
    if 'PROJECTQUOTA' not in settingkeys:
        settings.PROJECTQUOTA = 0 #unlimited
    if 'PROFILES' not in settingkeys:
        settings.PROFILES = []
    if 'INPUTSOURCES' not in settingkeys:
        settings.INPUTSOURCES = []
    if 'FORWARDERS' not in settingkeys:
        settings.FORWARDERS = []
    if 'PORT' not in settingkeys and not PORT:
        settings.PORT = 80
    if 'HOST' not in settingkeys and not HOST:
        settings.HOST = os.uname()[1]
    if 'URLPREFIX' not in settingkeys:
        settings.URLPREFIX = ''
    if 'REQUIREMEMORY' not in settingkeys:
        settings.REQUIREMEMORY = 0 #unlimited
    if 'MAXLOADAVG' not in settingkeys:
        settings.MAXLOADAVG = 0 #unlimited
    if 'MINDISKSPACE' not in settingkeys:
        if 'MINDISKFREE' in settingkeys:
            settings.MINDISKSPACE = settingkeys['MINDISKFREE']
        else:
            settings.MINDISKSPACE = 0
    if 'MAXCONCURRENTPROJECTSPERUSER' not in settingkeys:
        settings.MAXCONCURRENTPROJECTSPERUSER = 0 #unlimited
    if 'DISK' not in settingkeys:
        settings.DISK = None
    if 'STYLE' not in settingkeys:
        settings.STYLE = 'classic'
    if 'CLAMDIR' not in settingkeys:
        settings.CLAMDIR = os.path.dirname(os.path.abspath(__file__))
    if 'DISPATCHER' not in settingkeys:
        r = os.system('which clamdispatcher >/dev/null 2>/dev/null')
        if r == 0:
            settings.DISPATCHER = 'clamdispatcher'
        elif os.path.exists(settings.CLAMDIR + '/clamdispatcher.py') and stat.S_IXUSR & os.stat(settings.CLAMDIR + '/clamdispatcher.py')[stat.ST_MODE]:
            settings.DISPATCHER = settings.CLAMDIR + '/clamdispatcher.py'
        else:
            print("WARNING: clamdispatcher not found!!",file=sys.stderr)
            settings.DISPATCHER = 'clamdispatcher'
    if 'PROJECTS_PUBLIC' in settingkeys:
        print("NOTICE: PROJECTS_PUBLIC directive is obsolete and has no effect. You may be looking for LISTPROJECTS or ALLOWSHARE instead",file=sys.stderr)
    if 'REALM' not in settingkeys:
        settings.REALM = settings.SYSTEM_ID
    if 'DIGESTOPAQUE' not in settingkeys:
        settings.DIGESTOPAQUE = "%032x" % random.getrandbits(128) #TODO: not used now
    if 'ENABLEWEBAPP' not in settingkeys:
        settings.ENABLEWEBAPP = True
    if 'ENABLED' not in settingkeys:
        settings.ENABLED = True
    if 'QUICKTIMEOUT' not in settingkeys:
        settings.QUICKTIMEOUT = 90 #after loading output files for this many seconds, quick mode will be enabled and files will be loaded without metadata
    if 'REMOTEHOST' not in settingkeys:
        settings.REMOTEHOST = None
    elif 'REMOTEUSER' not in settingkeys:
        settings.REMOTEUSER = None
    if 'PREAUTHHEADER' not in settingkeys:
        settings.PREAUTHHEADER = None     #The name of the header field containing the pre-authenticated username
    elif isinstance(settings.PREAUTHHEADER,str):
        settings.PREAUTHHEADER = settings.PREAUTHHEADER.split(' ')
    else:
        settings.PREAUTHHEADER = None
    if 'USERS_MYSQL' not in settingkeys:
        settings.USERS_MYSQL = None
    if 'FORCEURL' not in settingkeys:
        settings.FORCEURL = None
    if 'CLAMFORCEURL' in os.environ:
        settings.FORCEURL = os.environ['CLAMFORCEURL']
    if 'USE_FORWARDED_HOST' not in settingkeys:
        settings.USE_FORWARDED_HOST = False
    if 'FORCEHTTPS' not in settingkeys:
        settings.FORCEHTTPS = settings.FORCEURL and settings.FORCEURL.startswith("https://")
    if 'PRIVATEACCESSTOKEN' not in settingkeys:
        settings.PRIVATEACCESSTOKEN = "%032x" % random.getrandbits(128)
    if 'OAUTH' not in settingkeys:
        settings.OAUTH = False
    if 'OAUTH_CLIENT_ID' not in settingkeys:
        settings.OAUTH_CLIENT_ID = settings.SYSTEM_ID
    if 'OAUTH_CLIENT_SECRET' not in settingkeys:
        settings.OAUTH_CLIENT_SECRET = ""
    if 'OAUTH_AUTH_URL' not in settingkeys:
        settings.OAUTH_AUTH_URL = ""
    if 'OAUTH_TOKEN_URL' not in settingkeys:
        settings.OAUTH_TOKEN_URL = ""
    if 'OAUTH_USERINFO_URL' not in settingkeys:
        settings.OAUTH_USERINFO_URL = ""
    if 'OAUTH_CLIENT_URL' not in settingkeys:
        if settings.FORCEURL:
            settings.OAUTH_CLIENT_URL = settings.FORCEURL
        else:
            settings.OAUTH_CLIENT_URL = None
    if 'OAUTH_REVOKE_URL' not in settingkeys:
        settings.OAUTH_REVOKE_URL = ""
    if 'OAUTH_SCOPE' not in settingkeys:
        settings.OAUTH_SCOPE = []
    if 'OAUTH_USERNAME_FUNCTION' not in settingkeys:
        settings.OAUTH_USERNAME_FUNCTION = clam.common.oauth.DEFAULT_USERNAME_FUNCTION
    if 'OAUTH_AUTH_FUNCTION' not in settingkeys:
        settings.OAUTH_AUTH_FUNCTION = clam.common.oauth.DEFAULT_AUTH_FUNCTION
    if 'SECRET_KEY' not in settingkeys:
        settings.SECRET_KEY = "%032x" % random.getrandbits(128) #not really used I think since we don't use flask.session
    if 'INTERFACEOPTIONS' not in settingkeys:
        settings.INTERFACEOPTIONS = ""
    if 'CUSTOMCSS' not in settingkeys:
        settings.CUSTOMCSS = ""
    if 'CUSTOMHTML_INDEX' not in settingkeys:
        if os.path.exists(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_index.html'):
            with io.open(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_index.html','r',encoding='utf-8') as f:
                settings.CUSTOMHTML_INDEX = f.read()
        else:
            settings.CUSTOMHTML_INDEX = ""
    if 'CUSTOMHTML_PROJECTSTART' not in settingkeys:
        if os.path.exists(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectstart.html'):
            with io.open(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectstart.html','r',encoding='utf-8') as f:
                settings.CUSTOMHTML_PROJECTSTART = f.read()
        else:
            settings.CUSTOMHTML_PROJECTSTART = ""
    if 'CUSTOMHTML_PROJECTDONE' not in settingkeys:
        if os.path.exists(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectdone.html'):
            with io.open(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectdone.html','r',encoding='utf-8') as f:
                settings.CUSTOMHTML_PROJECTDONE = f.read()
        else:
            settings.CUSTOMHTML_PROJECTDONE = ""
    if 'CUSTOMHTML_PROJECTFAILED' not in settingkeys:
        if os.path.exists(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectfailed.html'):
            with io.open(settings.CLAMDIR + '/static/custom/' + settings.SYSTEM_ID  + '_projectfailed.html','r',encoding='utf-8') as f:
                settings.CUSTOMHTML_PROJECTFAILED = f.read()
        else:
            settings.CUSTOMHTML_PROJECTFAILED = ""

    if 'CUSTOM_FORMATS' not in settingkeys:
        settings.CUSTOM_FORMATS = []
    clam.common.data.CUSTOM_FORMATS = settings.CUSTOM_FORMATS #dependency injection

    if 'CUSTOM_VIEWERS' not in settingkeys:
        settings.CUSTOM_VIEWERS = []
    clam.common.data.CUSTOM_VIEWERS = settings.CUSTOM_VIEWERS #dependency injection

    if 'ACTIONS' not in settingkeys:
        settings.ACTIONS = []

    if 'SESSIONDIR' not in settingkeys:
        settings.SESSIONDIR = os.path.join(settings.ROOT,'sessions')

    if 'ALLOW_ORIGIN' not in settingkeys:
        settings.ALLOW_ORIGIN = '*'
    if 'ASSUMESSL' not in settingkeys:
        settings.ASSUMESSL = settings.PORT == 443

    if 'BASICAUTH' not in settingkeys and (settings.USERS or settings.USERS_MYSQL or settings.USERS_FILE):
        settings.BASICAUTH = True #Allowing HTTP Basic Authentication
    elif 'BASICAUTH' not in settingkeys:
        settings.BASICAUTH = True #default is HTTP Basic

    if 'DIGESTAUTH' not in settingkeys and (settings.USERS or settings.USERS_MYSQL or settings.USERS_FILE):
        settings.DIGESTAUTH = True #Allowing HTTP Digest Authentication
    elif 'DIGESTAUTH' not in settingkeys:
        settings.DIGESTAUTH = True #allow digest by default for backward compatibility

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

    if not os.path.isdir(settings.ROOT + 'storage'):
        warning("Temporary storage directory does not exist yet, creating...")
        os.makedirs(settings.ROOT + 'storage')

    if not settings.PARAMETERS:
        warning("No parameters specified in settings module!")
    if not settings.USERS and not settings.USERS_MYSQL and not settings.USERS_FILE and not settings.PREAUTHHEADER and not settings.OAUTH:
        warning("No user authentication enabled, this is not recommended for production environments!")
    if settings.FORCEHTTPS:
        print("Forcing HTTPS", file=sys.stderr)
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
        if not settings.OAUTH_CLIENT_URL:
            error("You need to set OAUTH_CLIENT_URL to the base URL of your webservice, as it is known to the identity provider")

        warning("*** OAUTH is enabled, make sure you are running CLAM through HTTPS or security is void! ***")


def test_version():
    #Check version
    req = str(settings.REQUIRE_VERSION).split('.')
    ver = str(VERSION).split('.')

    uptodate = True
    for i in range(0,len(req)):
        if i < len(ver):
            if int(req[i]) > int(ver[i]):
                uptodate = False
                break
            elif int(ver[i]) > int(req[i]):
                break
    if not uptodate:
        error("Version mismatch: at least " + str(settings.REQUIRE_VERSION) + " is required")

def main():
    global settingsmodule, DEBUG, settings

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    settingsmodule = None
    PORT = HOST = FORCEURL = None
    PYTHONPATH = None
    ASSUMESSL = False

    parser = argparse.ArgumentParser(description="Start a CLAM webservice; turns command-line tools into RESTful webservice, including a web-interface for human end-users.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d','--debug',help="Enable debug mode", action='store_true', required=False)
    parser.add_argument('-H','--hostname', type=str,help="The hostname used to access the webservice", action='store',required=False)
    parser.add_argument('-p','--port', type=int,help="The port number for the webservice", action='store',required=False)
    parser.add_argument('-u','--forceurl', type=str,help="The full URL to access the webservice", action='store',required=False)
    parser.add_argument('-P','--pythonpath', type=str,help="Sets the $PYTHONPATH", action='store',required=False)
    parser.add_argument('-b','--basicauth', help="Default to HTTP Basic Authentication on the development server (do not expose to the world without SSL) (option remains for legacy purposes, enabled by default now)", action='store_true',required=False)
    parser.add_argument('-v','--version',help="Version", action='version',version="CLAM version " + str(VERSION))
    parser.add_argument('-c','--config', type=str,help="Path to external YAML configuration file to import", action='store',required=False)
    parser.add_argument('settingsmodule', type=str, help='The webservice service configuration to be imported. This is a Python module path rather than a file path (for instance: clam.config.textstats), the configuration must be importable by Python. Add the path where it is located using --pythonpath if it can not be found.')
    args = parser.parse_args()



    if 'debug' in args and args.debug:
        DEBUG = True
        setdebug(True)
    if 'port' in args:
        PORT = args.port
    if 'hostname' in args:
        HOST = args.hostname
    if 'forceurl' in args:
        FORCEURL = args.forceurl
    if 'pythonpath' in args:
        PYTHONPATH = args.pythonpath
    if 'basicauth' in args:
        ASSUMESSL = True
    if 'config' in args and args.config:
        os.environ['CONFIGFILE'] = args.config #passed through the environment

    settingsmodule = args.settingsmodule

    if PYTHONPATH:
        sys.path.append(PYTHONPATH)

    import_string = "import " + settingsmodule + " as settings"
    settings = importlib.import_module(settingsmodule)

    try:
        if settings.DEBUG:
            DEBUG = True
            setdebug(True)
            warning("DEBUG is enabled, never use this in publicly exposed environments as it is a security risk !!!")
    except: #not sure why?
        pass
    try:
        if settings.LOGFILE:
            setlogfile(settings.LOGFILE)
    except: #not sure why?
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
    if ASSUMESSL:
        settings.ASSUMESSL = ASSUMESSL

    if settings.URLPREFIX:
        settings.INTERNALURLPREFIX = settings.URLPREFIX
        warning("Using URLPREFIX in standalone mode! Are you sure this is what you want?")
        #raise Exception("Can't use URLPREFIX when running in standalone mode!")
    settings.URLPREFIX = '' #standalone server always runs at the root

    try:
        CLAMService('debug' if DEBUG else 'standalone') #start
    except socket.error:
        error("Unable to open socket. Is another service already running on this port?")

def run_wsgi(settings_module):
    """Run CLAM in WSGI mode"""
    global settingsmodule, DEBUG #pylint: disable=global-statement
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

if __name__ == '__main__':
    main()
