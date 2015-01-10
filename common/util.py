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


from __future__ import print_function, unicode_literals, division, absolute_import

import glob
import os
import sys
import datetime
if sys.version < '3':
    from urllib2 import Request
else:
    from urllib.request import Request #pylint: disable=E0611
import io

if sys.version < '3':
    from codecs import getwriter
    DEBUGLOG = getwriter('utf-8')(sys.stderr)
    LOG = getwriter('utf-8')(sys.stdout)
else:
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

def setlog(log):
    global LOG
    LOG = log

def setdebug(debug):
    global DEBUG
    DEBUG = debug

def printlog(msg):
    global LOG
    now = datetime.datetime.now()
    if LOG: LOG.write("------------------- [" + now.strftime("%d/%b/%Y %H:%M:%S") + "] " + msg + "\n")

def printdebug(msg):
    global DEBUG, DEBUGLOG
    if DEBUG: DEBUGLOG.write("CLAM DEBUG: " + msg + "\n")

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





class RequestWithMethod(Request):
  def __init__(self, *args, **kwargs):
    self._method = kwargs.get('method')
    if self._method:
        del kwargs['method']
    Request.__init__(self, *args, **kwargs)

  def get_method(self):
    return self._method if self._method else super(RequestWithMethod, self).get_method()
