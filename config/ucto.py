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

from common.parameters import *
from common.formats import *
from common.digestauth import pwhash

REQUIRE_VERSION = 0.2

SYSTEM_ID = "ucto"
SYSTEM_NAME = "Unicode Tokeniser"
SYSTEM_DESCRIPTION = "This is a tokeniser"

#Root directory for CLAM
ROOT = "/home/proycon/work/clamtmproot/"
URL = "http://localhost:8080"

#Users and passwords
USERS = None #Enable this instead if you want no authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 


#List of supported Input formats by the system
INPUTFORMATS = [ PlainTextFormat('utf-8',['txt']), TokenizedTextFormat('utf-8',['tok']) ]

#List of delivered Output formats by the system
OUTPUTFORMATS = [ TokenizedTextFormat('utf-8',['txt']), PlainTextFormat('utf-8',['tok']) ]

#The system command (Use the variables $STATUSFILE $DATAFILE $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY $USERNAME)
COMMAND = "/home/proycon/work/clam/tests/uctowrapper.sh $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY $PARAMETERS"

PARAMETERS =  [ 
    ('Main', [ 
        BooleanParameter('lowercase','-l','Lowercase','Convert text to lowercase',forbid=['uppercase']),
        BooleanParameter('uppercase','-u','Uppercase','Convert text to uppercase',forbid=['lowercase']),
        BooleanParameter('info','-i','Unicode Info','Show unicode information'),
        BooleanParameter('countwords','-cw','Count words','Count words'),
        BooleanParameter('sentok','-Ts','Sentence Tokenisation','Compute sentence boundaries'),
        BooleanParameter('crudetok','-TS','Crude tokenisation','Crude non-language-specific tokenisation', forbid=['tok']),
        BooleanParameter('verbose','-Tv','Verbose output','Verbose output'),
        ChoiceParameter('tok','-t','Tokenise for language','Tokenise for the specified language',[('nl','Nederlands'),('en','English')], nospace=True),
    ] )
]

