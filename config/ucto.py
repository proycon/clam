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
from clam.common.data import *
from clam.common.converters import *
from clam.common.digestauth import pwhash
from sys import path 

REQUIRE_VERSION = 0.5

SYSTEM_ID = "ucto"
SYSTEM_NAME = "Ucto Tokeniser"
SYSTEM_DESCRIPTION = "Ucto is a tokeniser designed for unicode (utf-8) texts. The tokeniser also supports some basic transformations."

#Root directory for CLAM
ROOT = path[0] + "/../ucto.clam/"
PORT = 8080

#Users and passwords
USERS = None #Enable this instead if you want no authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 


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
COMMAND = path[0] +  "/wrappers/uctowrapper.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY > $OUTPUTDIRECTORY/log"


PROFILES = [
    Profile(
        InputTemplate('untokinput', PlainTextFormat,"Text document", 
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),  
            ChoiceParameter(id='language',name='Language',description='The language this text is in', choices=[('en','English'),('nl','Dutch'),('fr','French'),('de','German'),('it','Italian')]),
            CharEncodingConverter(id='latin1',label='Convert from Latin-1 (iso-8859-1)',charset='iso-8859-1'),
            CharEncodingConverter(id='latin9',label='Convert from Latin-9 (iso-8859-15)',charset='iso-8859-15'),
            multi=True,
        ),
        ParameterCondition(verbose=True,
            then=OutputTemplate('vtokoutput', PlainTextFormat,"Verbosely Tokenised Text Document",
                ParameterCondition(sentenceperline=True,
                    then=SetMetaField('sentenceperline','yes')
                ),            
                ParameterCondition(lowercase=True,
                    then=SetMetaField('lowercase','yes')
                ),
                ParameterCondition(uppercase=True,
                    then=SetMetaField('uppercase','yes')
                ),
                copymetadata=True,
                extension='vtok',
                multi=True,
            ),
            otherwise=OutputTemplate('tokoutput', PlainTextFormat,"Tokenised Text Document",
                ParameterCondition(sentenceperline=True,
                    then=SetMetaField('sentenceperline','yes')
                ),
                ParameterCondition(lowercase=True,
                    then=SetMetaField('lowercase','yes')
                ),
                ParameterCondition(uppercase=True,
                    then=SetMetaField('uppercase','yes')
                ),
                copymetadata=True,
                extension='tok',
                multi=True,
            )
        )
    ),
]

PARAMETERS =  [ 
    ('Tokenisation options', [
        BooleanParameter('verbose','Verbose tokeniser output','Outputs token types per token, one token per line',paramflag='-v'),
        BooleanParameter('sentenceperline','Sentence per line','Output each sentence on a single line', paramflag='-s'),
        BooleanParameter('lowercase','Lowercase','Convert text to lowercase',forbid=['uppercase'], paramflag='-u'),
        BooleanParameter('uppercase','Uppercase','Convert text to uppercase',forbid=['lowercase'], paramflag='-l'),
    ]),
]

