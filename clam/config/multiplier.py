#!/usr/bin/env python3
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Service Configuration File (Template) --
#       by Maarten van Gompel (proycon)
#       Centre for Language Studies
#       Radboud University Nijmegen
#
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       http://proycon.github.com/clam
#
#       Licensed under GPLv3
#
###############################################################

#This is an example for CLAM showing the use of Actions


from clam.common.parameters import *
from clam.common.formats import *
from clam.common.converters import *
from clam.common.viewers import *
from clam.common.data import *
from clam.common.digestauth import pwhash
import sys

REQUIRE_VERSION = "0.99"

# ======== GENERAL INFORMATION ===========

# General information concerning your system.


#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "multiplier"

#System name, the way the system is presented to the world
SYSTEM_NAME = "Multiplier"

#An informative description for this system (this should be fairly short, about one paragraph, and may not contain HTML)
SYSTEM_DESCRIPTION = "Example of CLAM Actions, simple multiplication of two numbers"

# ======== LOCATION ===========

#The root directory for CLAM, all project files, (input & output) and
#pre-installed corpora will be stored here. Set to an absolute path:
ROOT = "/tmp/clammultiplier.projects/"

#The URL of the system (If you start clam with the built-in webserver, you can override this with -P)
PORT= 8080

#The hostname of the system. Will be automatically determined if not set. (If you start clam with the built-in webserver, you can override this with -H)
#Users *must* make use of this hostname and no other (even if it points to the same IP) for the web application to work.
#HOST = 'localhost'

#If the webservice runs in another webserver (e.g. apache, nginx, lighttpd), and it
#doesn't run at the root of the server, you can specify a URL prefix here:
#URLPREFIX = "/myservice/"

#Optionally, you can force the full URL CLAM has to use, rather than rely on any autodetected measures:
#FORCEURL = "http://myclamservice.com"

#The location of where CLAM is installed (will be determined automatically if not set)
#CLAMDIR = "/path/to/clam"



# ======== AUTHENTICATION & SECURITY ===========

#Users and passwords

#set security realm, a required component for hashing passwords (will default to SYSTEM_ID if not set)
#REALM = SYSTEM_ID

USERS = None #no user authentication/security (this is not recommended for production environments!)

ADMINS = None #List of usernames that are administrator and can access the administrative web-interface (on URL /admin/)

#If you want to enable user-based security, you can define a dictionary
#of users and (hashed) passwords here. The actual authentication will proceed
#as HTTP Digest Authentication. Although being a convenient shortcut,
#using pwhash and plaintext password in this code is not secure!!

#USERS = { user1': '4f8dh8337e2a5a83734b','user2': pwhash('username', REALM, 'secret') }

#Amount of free memory required prior to starting a new process (in MB!), Free Memory + Cached (without swap!). Set to 0 to disable this check (not recommended)
REQUIREMEMORY = 10

#Maximum load average at which processes are still started (first number reported by 'uptime'). Set to 0 to disable this check (not recommended)
MAXLOADAVG = 1.0

#Minimum amount of free diskspace in MB. Set to 0 to disable this check (not recommended)
DISK = '/dev/sda1' #set this to the disk where ROOT is on
MINDISKSPACE = 10


# ======== WEB-APPLICATION STYLING =============

#Choose a style (has to be defined as a CSS file in clam/style/ ). You can copy, rename and adapt it to make your own style
STYLE = 'classic'

# ======== PROFILE DEFINITIONS ===========

#No profiles, we only use actions
PROFILES = []

# ======== COMMAND ===========

#No command is used, we only use actions
COMMAND = None

# ======== PARAMETER DEFINITIONS ===========

#No global parameters, we only use actions

#The parameters are subdivided into several groups. In the form of a list of (groupname, parameters) tuples. The parameters are a list of instances from common/parameters.py

PARAMETERS =  []


def multiply(x,y):
    return x * y

# ======== ACTIONS ===========

ACTIONS = [
    Action(id="multiply",name="Multiplier",description="Multiply two numbers", function=multiply, parameters=[
            IntegerParameter(id="x", name="First value", required=True),
            IntegerParameter(id="y", name="Second value", required=True)
    ])
]


# ======== DISPATCHING (ADVANCED! YOU CAN SAFELY SKIP THIS!) ========

#The dispatcher to use (defaults to clamdispatcher.py), you almost never want to change this
#DISPATCHER = 'clamdispatcher.py'

#DISPATCHER_POLLINTERVAL = 30   #interval at which the dispatcher polls for resource consumption (default: 30 secs)
#DISPATCHER_MAXRESMEM = 0    #maximum consumption of resident memory (in megabytes), processes that exceed this will be automatically aborted. (0 = unlimited, default)
#DISPATCHER_MAXTIME = 0      #maximum number of seconds a process may run, it will be aborted if this duration is exceeded.   (0=unlimited, default)
#DISPATCHER_PYTHONPATH = []        #list of extra directories to add to the python path prior to launch of dispatcher

#Run background process on a remote host? Then set the following (leave the lambda in):
#REMOTEHOST = lambda: return 'some.remote.host'
#REMOTEUSER = 'username'

#For this to work, the user under which CLAM runs must have (passwordless) ssh access (use ssh keys) to the remote host using the specified username (ssh REMOTEUSER@REMOTEHOST)
#Moreover, both systems must have access to the same filesystem (ROOT) under the same mountpoint.
