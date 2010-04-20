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

# *** DO NOT ALTER THIS FILE, MAKE A COPY INSTEAD! ***

from common.parameters import *
from common.formats import *
from common.digestauth import pwhash

REQUIRE_VERSION = 0.2

#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "clam"

#System name, the way the system is presented to the world
SYSTEM_NAME = "CLAM: Computional Linguistics Application Mediator"

#An informative description for this system:
SYSTEM_DESCRIPTION = "CLAM is a webservice wrapper around NLP tools"

#The root directory for CLAM, all project files, (input & output) and
#pre-installed corpora will be stored here. Set to an absolute path:
ROOT = ""

#The URL of the system
URL = "http://localhost:8080"

#Users and passwords
USERS = None #no user authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 

#Do you want all projects to be public to all users? Otherwise projects are 
#private and only open to their owners and users explictly granted access.
PROJECTS_PUBLIC = True

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
#     $CONFFILE        - Filename of the clam.xml file describing the 
#                        system and chosen configuration.
#     $USERNAME        - The username of the currently logged in user
#                        (set to "anonymous" if there is none)
#     $PARAMETERS      - List of chosen parameters, using the specified flags
#
COMMAND = ""

#Example:
#COMMAND = "/home/proycon/work/clam/tests/uctowrapper.sh $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY $PARAMETERS"

PARAMETERS = []

#List of supported Input formats by the system
INPUTFORMATS = []

#List of delivered Output formats by the system (it's not mandatory for all these filetypes to be delivered)
OUTPUTFORMATS = []

