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
from sys import path 

REQUIRE_VERSION = 0.2

SYSTEM_ID = "tadpole"
SYSTEM_NAME = "Tadpole"
SYSTEM_DESCRIPTION = "Tadpole is a suite containing a tokeniser, pos-tagger, lemmatiser, morphological analyser, and dependency parser."

#Root directory for CLAM
ROOT = path[0] + "/../tadpole.clam/"
PORT = 8080
URL = "http://localhost:" + str(PORT)

#Users and passwords
USERS = None #Enable this instead if you want no authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 


#List of supported Input formats by the system
INPUTFORMATS = [ PlainTextFormat('utf-8',['txt']), TokenizedTextFormat('utf-8',['tok']) ]

#List of delivered Output formats by the system
OUTPUTFORMATS = [ TadpoleFormat('utf-8',['tadpole']) ]

#The system command (Use the variables $STATUSFILE $DATAFILE $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY $USERNAME)
COMMAND = path[0] +  "/wrappers/tadpolewrapper.sh $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY $PARAMETERS"

PARAMETERS =  [ 
    ('Components', [
    ChoiceParameter('parser','--skip=', 'Skip components','Skip selected components. You may especially want to skip the dependency parser if you do not need it, as it takes a lot of resources.', [('p','Dependency Parser'),('m','Morphological Analyser'),('t','Tokeniser')], multi=True, delimiter='',default=['p'] )
    ])
]

