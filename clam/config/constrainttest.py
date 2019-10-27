#!/usr/bin/env python
#-*- coding:utf-8 -*-


###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Settings --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       Licensed under GPLv3
#
###############################################################

from clam.common.parameters import *
from clam.common.formats import *
from clam.common.converters import *
from clam.common.viewers import *
from clam.common.data import *
from clam.common.digestauth import pwhash
import clam
import sys

REQUIRE_VERSION = 3.0
CLAMDIR = clam.__path__[0]

# ======== GENERAL INFORMATION ===========

#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "constrainttest"

#System name, the way the system is presented to the world
SYSTEM_NAME = "Constraint Test (CLAM Demo)"

#An informative description for this system:
SYSTEM_DESCRIPTION = "This webservice provides a frequency list of the number of PoS tags in a FoLiA documents"

SYSTEM_URL = "https://proycon.github.io/clam"

SYSTEM_LICENSE = "GNU Public License v3"

SYSTEM_AUTHOR = "proycon"

SYSTEM_AFFILIATION = "Centre for Language and Speech Technology, Radboud University"

SYSTEM_EMAIL = "proycon@anaproy.nl"



# ======== LOCATION ===========

#The root directory for CLAM, all project files, (input & output) and
#pre-installed corpora will be stored here. Set to an absolute path:
ROOT = "/tmp/clam.constrainttest/"

#The URL of the system
PORT= 8080

# ======== AUTHENTICATION & SECURITY ===========

#Users and passwords
USERS = None #no user authentication
#USERS = { 'admin': pwhash('admin', SYSTEM_ID, 'secret'), 'proycon': pwhash('proycon', SYSTEM_ID, 'secret'), 'antal': pwhash('antal', SYSTEM_ID, 'secret') , 'martin': pwhash('martin', SYSTEM_ID, 'secret') }

ADMINS = ['anonymous'] #Define which of the above users are admins (never set this to anonymous on a real webservice!!!!)
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!!


#Instead of specifying variables like we did above, we can include them from an external configuration file automatically
#This invokes the automatic loader, it will try to find a file named $hostname.yaml (or yml), where $hostname
#is the auto-detected hostname of this system. Alternatively, it tries a static config.yml .
#You can also set an environment variable CONFIGFILE to specify the exact file to load at run-time.
#It will look in several paths including the current working directory and the path this settings script is loaded from.
#Such an external configuration file simply defines variables that will be imported here. If it fails to find
#a configuration file, an exception will be raised.
loadconfig(__name__)

#Amount of free memory required prior to starting a new process (in MB!), Free Memory + Cached (without swap!)
#REQUIREMEMORY = 10

#Maximum load average at which processes are still started (first number reported by 'uptime')
#MAXLOADAVG = 4.0

#The amount of diskspace a user may use (in MB), this is a soft quota which can be exceeded, but creation of new projects is blocked until usage drops below the quota again
USERQUOTA = 10

# ======== WEB-APPLICATION STYLING =============

#Choose a style (has to be defined as a CSS file in style/ )
STYLE = 'classic'

# ======= INTERFACE OPTIONS ===========

#allow CLAM to download its input from a user-specified url
INTERFACEOPTIONS = "inputfromweb"


CUSTOMHTML_INDEX = "<p>This is a <strong>CLAM</strong> demo</p>"
#CUSTOMHTML_PROJECTSTART = ""
#CUSTOMHTML_PROJECTDONE = ""


# ======== PREINSTALLED DATA ===========

#INPUTSOURCES = [
#    InputSource(id='sampledocs',label='Sample texts',path=ROOT+'/inputsources/sampledata',defaultmetadata=PlainTextFormat(None, encoding='utf-8') ),
#]

# ======== PROFILE DEFINITIONS ===========

PROFILES = [
    Profile(
        InputTemplate('foliainput', FoLiAXMLFormat,"Input document (FoLiA)",
            RequireMeta(**{"pos-annotation_exists": True}),
            extension='.folia.xml',
            multi=True,
            acceptarchive=True,
        ),
        #------------------------------------------------------------------------------------------------------------------------
        OutputTemplate('posfreqlist', PlainTextFormat,'PoS frequency list',
            SetMetaField('encoding','utf-8'),
            SimpleTableViewer(),
            filename='posfreqlist.tsv',
            unique=True
        ),
    )
]

# ======== COMMAND ===========

#The system command. It is recommended you set this to small wrapper
#script around your actual system. Full shell syntax is supported. Using
#absolute paths is preferred. The current working directory will be
#set to the project directory.
#
#You can make use of the following special variables,
#which will be automatically set by CLAM:
#     $INPUTDIRECTORY  - The directory where input files are uploaded.
#     $OUTPUTDIRECTORY - The directory where the system should output
#                        its output files.
#     $STATUSFILE      - Filename of the .status file where the system
#                        should output status messages.
#     $DATAFILE        - Filename of the clam.xml file describing the
#                        system and chosen configuration.
#     $USERNAME        - The username of the currently logged in user
#                        (set to "anonymous" if there is none)
#     $PARAMETERS      - List of chosen parameters, using the specified flags
#
COMMAND = CLAMDIR + "/wrappers/constrainttest.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY"

# ======== PARAMETER DEFINITIONS ===========

#The parameters are subdivided into several groups. In the form of a list of (groupname, parameters) tuples. The parameters are a list of instances from common/parameters.py
PARAMETERS =  []

