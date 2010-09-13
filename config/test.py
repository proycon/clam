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
from clam.common.digestauth import pwhash
import sys

REQUIRE_VERSION = 0.2

#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "clamtest"

#System name, the way the system is presented to the world
SYSTEM_NAME = "CLAM Demo"

#An informative description for this system:
SYSTEM_DESCRIPTION = "This is a small demo for CLAM. It does not really do anything useful but simply shows some of CLAM's abilities. Most of the parameters you can configure below don't have any real function. All the system will do is reverse all letters in the files you upload and output a log file with some information about the parameters."

#The root directory for CLAM, all project files, (input & output) and
#pre-installed corpora will be stored here. Set to an absolute path:
ROOT = "/home/proycon/work/clamtmproot2/"

#The URL of the system
#URL = "http://localhost:8080"
PORT= 8080

#Users and passwords
USERS = None #no user authentication
#USERS = { 'admin': pwhash('admin', SYSTEM_ID, 'secret'), 'proycon': pwhash('proycon', SYSTEM_ID, 'secret'), 'antal': pwhash('antal', SYSTEM_ID, 'secret') , 'martin': pwhash('martin', SYSTEM_ID, 'secret') }

ADMINS = ['admin'] #Define which of the above users are admins
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 

#Do you want all projects to be public to all users? Otherwise projects are 
#private and only open to their owners and users explictly granted access.
PROJECTS_PUBLIC = False

#List of supported Input formats by the system
#New format types should be added to common/formats.py, and can then be used here:
INPUTFORMATS = [ PlainTextFormat('utf-8',['txt']) ]

#List of delivered Output formats by the system (it's not mandatory for all these filetypes to be delivered at the same time)
OUTPUTFORMATS = [ PlainTextFormat('utf-8',['txt']) ]

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
COMMAND = sys.path[0] + "/tests/testwrapper.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY $PARAMETERS > $OUTPUTDIRECTORY/log"

#The parameters are subdivided into several group. In the form of a list of (groupname, parameters) tuples. The parameters are a list of instances from common/parameters.py
PARAMETERS =  [ 
    ('Main', [ 
        BooleanParameter('boolean','-b','Boolean','To be or not to be? That is the question'),
        IntegerParameter('integer','-i','Integer','Integer between zero and ten',minvalue=0, maxvalue=10),
        FloatParameter('float','-f','Float','Float between 0.0 and 1.0',minvalue=0.0, maxvalue=1.0),
        StringParameter('string','-s','String','Enter a word'),
        TextParameter('text','-t','String','Text'),
        ChoiceParameter('colourchoice','-c','Choice','Favourite colour',choices=[('red','red'),('green','green'),('blue','blue')]),
        ChoiceParameter('cities','-C', 'Visited cities', 'What cities have you visited?', choices=[('amsterdam', 'Amsterdam'), ('ny', 'New York'), ('london', 'London'), ('paris','Paris')], multi=True)
    ] )
]

