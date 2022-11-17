#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- General purpose utility functions --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       Licensed under GPLv3
#
###############################################################

#pylint: disable=global-statement

import glob
import os
import sys
import datetime
import io

DEBUGLOG = sys.stderr
LOG = sys.stdout

DEBUG = False

def globsymlinks(pattern, recursion=True):
    for f in glob.glob(pattern):
        if os.path.islink(f):
            yield f, os.readlink(f)
    if recursion:
        for d in os.listdir(os.path.dirname(pattern)):
            if os.path.isdir(d):
                for linkf,realf in globsymlinks(d + '/' + os.path.basename(pattern),recursion):
                    yield linkf,realf

def computediskusage(path):
    total_size = 0
    total_files = 0
    for dirpath, dirnames, filenames in os.walk(path): #pylint: disable=unused-variable
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
                total_files += 1
            except:
                #may happen in case of dangling symlinks
                pass
    return total_size / 1024 / 1024, total_files #MB


def setlog(log):
    global LOG
    LOG = log

def setdebug(debug):
    global DEBUG
    DEBUG = debug

def printlog(msg):
    if LOG:
        now = datetime.datetime.now()
        LOG.write("[" + now.strftime("%d/%b/%Y %H:%M:%S") + "] " + msg + "\n")

def printdebug(msg):
    if DEBUG:
        now = datetime.datetime.now()
        DEBUGLOG.write("[" + now.strftime("%d/%b/%Y %H:%M:%S") + " DEBUG] " + msg + "\n")

def setlogfile(filename):
    global LOG, DEBUGLOG
    LOG = DEBUGLOG = io.open(filename,'w', encoding='utf-8')

def xmlescape(s):
    begin = -1
    s2 = ""
    for i,c in enumerate(s):
        if c == '&':
            begin = i
        elif c == ';':
            if begin > -1:
                s2 += s[begin:i+1]
                begin = -1
            else:
                s2 += c
        elif c == ' ':
            if begin != -1:
                s2 += "&amp;" + s[begin+1:i+1]
                begin = -1
            else:
                s2 += c
        elif c == '<':
            s2 += "&lt;"
        elif c == '>':
            s2 += "&gt;"
        elif c == '"':
            s2 += "&quot;"
        elif begin == -1:
            s2 += c
    if begin != -1:
        s2 += "&amp;" + s[begin+1:]
    s = s2
    return s



def withheaders(response, contenttype="text/xml; charset=UTF-8", headers=None, cookies=None, cookies_max_age=None):
    if headers is None: headers = { }
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Type'] = contenttype
    try:
        for key, value in headers.items():
            if key == 'allow_origin':
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
                response.headers['Access-Control-Allow-Headers'] = 'Authorization'
                key = 'Access-Control-Allow-Origin'
            response.headers[key] = value
    except AttributeError: #no dictionary? could be generator/list of tuples
        for key, value in headers:
            if key == 'allow_origin':
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
                response.headers['Access-Control-Allow-Headers'] = 'Authorization'
                key = 'Access-Control-Allow-Origin'
            response.headers[key] = value

    if cookies:
        assert isinstance(cookies, dict)
        for key, value in cookies.items():
            if value is not None and value != "":
                response.set_cookie(key, value, cookies_max_age)
    return response

def isncname(name):
    """Checks if a name is a valid XML NCName"""
    #not entirely according to specs http://www.w3.org/TR/REC-xml/#NT-Name , but simplified:
    for i, c in enumerate(name):
        if i == 0:
            if not c.isalpha() and c != '_':
                raise ValueError('Invalid XML NCName identifier: ' + name + ' (at position ' + str(i+1)+')')
        else:
            if not c.isalnum() and not (c in ['-','_','.']):
                raise ValueError('Invalid XML NCName identifier: ' + name + ' (at position ' + str(i+1)+')')
    return True

def makencname(name, prefix="I"):
    """Convert the name to a valid XML NCName, simply dropping characters that are invalid"""
    ncname = ""
    for i, c in enumerate(name):
        if i == 0:
            if not c.isalpha() and c != '_':
                ncname += prefix
        if c.isalnum() or c in ('-','_','.'):
            ncname += c
    if not ncname:
        raise ValueError("Unable to convert '" + str(name) + "' to a valid XML NCName")
    return ncname

def parse_accept_header(request):
    """Get the outputtype based on content negotiation"""
    if 'Accept' in request.headers:
        accept = request.headers['Accept']
        printdebug("Found accept header: " + str(accept))
        if accept:
            accept = accept.split(",")
            ordered = []
            for item in accept:
                item = item.split(";")
                q = 1.0
                if len(item) > 1:
                    if item[1].startswith("q="):
                        try:
                            q = float(item[1][2:])
                        except ValueError:
                            q = 1.0
                ordered.append( (item[0],q) )

            #sort by q value
            ordered.sort(key=lambda x: -1 * x[1])
            return [ x[0] for x in ordered ]
    return []
