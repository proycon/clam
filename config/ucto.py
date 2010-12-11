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

SYSTEM_ID = "ucto"
SYSTEM_NAME = "Unicode Tokeniser"
SYSTEM_DESCRIPTION = "Ucto is a tokeniser designed for unicode (utf-8) texts. Furthermore, it is also an inspection tool for examining the nature or count of the characters in a text. Support also exists for some basic transformations."

#Root directory for CLAM
ROOT = path[0] + "/../ucto.clam/"
PORT = 8080
URL = "http://localhost:" + str(PORT)

#Users and passwords
USERS = None #Enable this instead if you want no authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 


#List of supported Input formats by the system
INPUTFORMATS = [ PlainTextFormat('utf-8',['txt']), TokenizedTextFormat('utf-8',['tok']) ]

#List of delivered Output formats by the system
OUTPUTFORMATS = [ TokenizedTextFormat('utf-8',['tok']) ]

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
COMMAND = path[0] +  "/wrappers/uctowrapper.sh $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY $PARAMETERS"

PARAMETERS =  [ 
    ('Tokenisation', [
        ChoiceParameter('tok','-t','Tokenise for language','Tokenise for the specified language',choices=[('','No language-specific tokenisation'),('nl','Nederlands'),('en','English')], nospace=True), #note that when an empty value is selected,   
        BooleanParameter('sentok','-Ts','Sentence Tokenisation','Compute sentence boundaries'),
        BooleanParameter('crudetok','-TS','Crude tokenisation','Crude non-language-specific tokenisation', forbid=['tok']),
        BooleanParameter('verbose','-Tv','Verbose tokeniser output','Outputs token types per token, one token per line', require=['tok']),
    ]),
    ('Transformations', [ 
        BooleanParameter('lowercase','-l','Lowercase','Convert text to lowercase',forbid=['uppercase']),
        BooleanParameter('uppercase','-u','Uppercase','Convert text to uppercase',forbid=['lowercase']),
        BooleanParameter('reverse','-r','Reverse words','Reverses all the words in a line'),
        BooleanParameter('bigrams','-2','List bigrams','',forbid=['trigrams','quadgrams']),
        BooleanParameter('trigrams','-3','List trigrams','',forbid=['bigrams','quadgrams']),
        BooleanParameter('quadgrams','-4','List quadgrams','',forbid=['bigrams','trigrams']),
    ]),
    ('Word and Character Information', [
        BooleanParameter('info','-i','Unicode Info','Show unicode information per character, one per line'),
        BooleanParameter('countwords','-cw','Count words','Count words'),
    	BooleanParameter('countchars','-cc','Count characters (without spaces and punctuation)'),
    	BooleanParameter('countchars2','-cs','Count characters (with spaces and punctuation)'),
    ])
]

