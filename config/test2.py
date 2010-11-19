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
from clam.common.metadata import *
from clam.common.digestauth import pwhash
import sys

REQUIRE_VERSION = 0.5

# ======== GENERAL INFORMATION ===========

#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "clamtest2"

#System name, the way the system is presented to the world
SYSTEM_NAME = "CLAM Demo - Text Statistics"

#An informative description for this system:
SYSTEM_DESCRIPTION = "This is a small demo for CLAM. It computes several statistics for plaintext files."

# ======== LOCATION ===========

#The root directory for CLAM, all project files, (input & output) and
#pre-installed corpora will be stored here. Set to an absolute path:
ROOT = sys.path[0] + "/clamtestroot2/"

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

# ======== ENABLED FORMATS ===========

#Here you can specify an extra formats module
CUSTOM_FORMATS_MODULE = None

# ======== PROFILE DEFINITIONS ===========

PROFILES = [ 
    Profile(
        InputTemplate('textinput', PlainTextFormat,"Plain-text document",  
            ChoiceParameter(id='encoding',name='Encoding',description='The character encoding of the file', choices=[('utf-8','UTF-8 Unicode'), ('latin1','Latin 1')]),  
            ChoiceParameter(id='language',name='Language',description='The language the text is in', choices=[('en','English'),('nl','Dutch'),('fr','French')]),
            extension='.txt',
            multi=True
        ),
        OutputTemplate('statsbydoc',PlainTextFormat,'Document Statistics',
            extension='.stats',
            multi=True
        ),
        OutputTemplate('freqlistbydoc', PlainTextFormat,'Document Frequency list ', 
            CopyMetaField('textinput.language'), 
            extension='.freqlist',
            multi=True
        ),
        OutputTemplate(id='overallstats', formatclass=PlainTextFormat, label='Overall Statistics',
            filename='overall.stats',
            unique=True
        ), 
        OutputTemplate(id='overallfreqlist', formatclass=PlainTextFormat, label='Overall Frequency List',
            filename='overall.freqlist',
            unique=True
        ), 
        ParameterCondition(createlexicon=True, 
            then= OutputTemplate(id='lexicon', formatclass=PlainTextFormat, label='Lexicon',
                filename='overall.lexikon',
                unique=True
            )            
        )
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
COMMAND = sys.path[0] + "/tests/test2.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY $PARAMETERS > $OUTPUTDIRECTORY/log"

# ======== PARAMETER DEFINITIONS ===========

#The parameters are subdivided into several groups. In the form of a list of (groupname, parameters) tuples. The parameters are a list of instances from common/parameters.py
PARAMETERS =  [ 
    ('Main', [ 
        BooleanParameter(id='createlexicon',name='Create Lexicon',description='Generate a seperate overall lexicon?'),
        IntegerParameter(id='freqlistlimit',name='Limit frequencylist',description='Limit entries in frequencylist to the top scoring ones. Value of one or higher',minvalue=0, maxvalue=99999999),
    ] )
]

