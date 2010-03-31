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

from parameters import *
from formats import *

SYSTEM_ID = "ucto"
SYSTEM_NAME = "Unicode Tokeniser"
SYSTEM_DESCRIPTION = "This is a tokeniser"

#Root directory for CLAM
ROOT = "/home/proycon/work/clamtmproot/"
URL = "http://localhost:8080"

#List of supported Input formats by the system
INPUTFORMATS = [ PlainTextFormat(['.txt']), TokenizedTextFormat(['.toktxt']) ]

#List of delivered Output formats by the system
OUTPUTFORMATS = [ TokenizedTextFormat(['.txt']), PlainTextFormat(['.toktxt']) ]

#The system command (Use the variables $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY)
COMMAND = "uctowrapper.sh $INPUTDIRECTORY $OUTPUTDIRECTORY $PARAMETERS"

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

