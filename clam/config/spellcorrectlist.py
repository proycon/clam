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
import sys

REQUIRE_VERSION = 0.5

# ======== GENERAL INFORMATION ===========

#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "spellcorrectlist"

#System name, the way the system is presented to the world
SYSTEM_NAME = "Spelling correction based on Errorlist (Demo)"

#An informative description for this system:
SYSTEM_DESCRIPTION = "This webservice spellchecks tokenised (plain text) files by comparing every word to an errorlist. It is a demo for IL."

# ======== LOCATION ===========

#The root directory for CLAM, all project files, (input & output) and
#pre-installed corpora will be stored here. Set to an absolute path:
ROOT = "/tmp/clam.spellcorrectlist/"

#The URL of the system
PORT= 8080

# ======== AUTHENTICATION & SECURITY ===========

#Users and passwords
USERS = None #no user authentication
#USERS = { 'admin': pwhash('admin', SYSTEM_ID, 'secret'), 'proycon': pwhash('proycon', SYSTEM_ID, 'secret'), 'antal': pwhash('antal', SYSTEM_ID, 'secret') , 'martin': pwhash('martin', SYSTEM_ID, 'secret') }

ADMINS = ['admin'] #Define which of the above users are admins
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 

#Do you want all projects to be public to all users? Otherwise projects are 
#private and only open to their owners and users explictly granted access.
PROJECTS_PUBLIC = False

#Amount of free memory required prior to starting a new process (in MB!), Free Memory + Cached (without swap!)
REQUIREMEMORY = 10

#Maximum load average at which processes are still started (first number reported by 'uptime')
MAXLOADAVG = 1.0


# ======== WEB-APPLICATION STYLING =============

#Choose a style (has to be defined as a CSS file in style/ )
STYLE = 'classic'

# ======== ENABLED FORMATS ===========

#Here you can specify an extra formats module
CUSTOM_FORMATS_MODULE = None


# ======== PREINSTALLED DATA ===========

#INPUTSOURCES = [
#    InputSource(id='sampledocs',label='Sample texts',path=ROOT+'/inputsources/sampledata',defaultmetadata=PlainTextFormat(None, encoding='utf-8') ),
#]

# ======== PROFILE DEFINITIONS ===========

PROFILES = [ 
    Profile(
        InputTemplate('textinput',PlainTextFormat,"Input text document",  
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),  
            StaticParameter(id='language',name='Language',description='The language the text is in', value='Dutch'),
            #StringParameter(id='author',name='Author',description="The author's name", maxlength=100),
            #IntegerParameter(id='year',name='Year of Publication',description="The year of publication", minvalue=1900,maxvalue=2030),
            #InputSource(id='sampledoc', label="Sample Document", path=ROOT+'/inputsources/sampledoc.txt', metadata=PlainTextFormat(None, encoding='utf-8',language='en')),
            extension='.txt',
            multi=False
        ),
        InputTemplate('listinput',PlainTextFormat,"Errolist input",  
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),  
            StaticParameter(id='language',name='Language',description='The language the text is in', value='Dutch'),
            StringParameter(id='author',name='Author',description="The author's name", maxlength=100),
            #IntegerParameter(id='year',name='Year of Publication',description="The year of publication", minvalue=1900,maxvalue=2030),
            #InputSource(id='sampledoc', label="Sample Document", path=ROOT+'/inputsources/sampledoc.txt', metadata=PlainTextFormat(None, encoding='utf-8',language='en')),
            extension='.txt',
            multi=False
        ),
        OutputTemplate('textoutput',PlainTextFormat,"Corrected version of input document",
            SetMetaField('encoding','ascii'),
            removeextension='.txt',
            extension='.spellcorrectlist',
            multi=False
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
COMMAND = sys.path[0] + "/wrappers/spellcorrectlist.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY"

# ======== PARAMETER DEFINITIONS ===========

#The parameters are subdivided into several groups. In the form of a list of (groupname, parameters) tuples. The parameters are a list of instances from common/parameters.py
PARAMETERS =  [ 
    ('Main', [ 
        ChoiceParameter(id='casesensitive',name='Case Sensitivity',description='Enable case sensitive behaviour?', choices=['yes','no'],default='yes'),
        StringParameter(id='author',name='Author',description='Sign output metadata with the specified author name',maxlength=255),
    ] )
]

