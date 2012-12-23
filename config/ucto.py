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
from os import uname, environ
from base64 import b64decode as D

REQUIRE_VERSION = 0.7

SYSTEM_ID = "ucto"
SYSTEM_NAME = "Ucto Tokeniser"
SYSTEM_DESCRIPTION = 'Ucto is a unicode-compliant tokeniser. It takes input in the form of one or more untokenised texts, and subsequently tokenises them. Several languages are supported, but the software is extensible to other languages.'

#Root directory for CLAM
ROOT = path[0] + "/../ucto.clam/"
PORT = 8080

#Users and passwords
USERS = None #Enable this instead if you want no authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 


# ================ Server specific configurations for CLAM ===============
host = uname()[1]
if host == 'galactica' or host == 'roma': #proycon's laptop/server
    CLAMDIR = "/home/proycon/work/clam"
    ROOT = "/home/proycon/work/ucto.clam/"
    PORT = 9001
    BINDIR = "/home/proycon/local/bin/"
elif host == 'applejack': #Nijmegen
    if not 'CLAMTEST' in environ:
        #live production environment/
        CLAMDIR = "/scratch2/www/webservices-lst/live/repo/clam"
        ROOT = "/scratch2/www/webservices-lst/live/writable/ucto/"
        HOST = "webservices-lst.science.ru.nl"
        PORT = 80    
    else:
        #test environment
        CLAMDIR = "/scratch2/www/webservices-lst/test/repo/clam"
        ROOT = "/scratch2/www/webservices-lst/test/writable/ucto/"
        HOST = "webservices-lst.science.ru.nl"
        PORT = 81        
    URLPREFIX = "ucto"
    BINDIR = "/vol/customopt/uvt-ru/bin/"    
    USERS_MYSQL = {
        'host': 'mysql-clamopener.science.ru.nl', 
        'user': 'clamopener',        
        'password': D(open(environ['CLAMOPENER_KEYFILE']).read().strip()),
        'database': 'clamopener',
        'table': 'clamusers_clamusers'
    }
    REALM = "WEBSERVICES-LST"
elif host == 'echo' or host == 'nomia' or host == 'echo.uvt.nl' or host == 'nomia.uvt.nl': #Tilburg    
    #Assuming ILK server
    CLAMDIR = "/var/www/clam"
    BINDIR = "/var/www/bin/"
    ROOT = "/var/www/clamdata/ucto/"
    HOST = 'webservices.ticc.uvt.nl'
    PORT = 80
    URLPREFIX = 'ucto'
    #WEBSERVICEGHOST = 'ws'
    #REALM = 'CLAM-TICC'
    #USERS_MYSQL = {
    #    'host': 'stheno.uvt.nl',
    #    'user': 'clamopener',
    #    'password': '',
    #    'database': 'clamopener',
    #    'table': 'clamusers_clamusers',        
    #}
else:
    raise Exception("I don't know where I'm running from! Got " + host)    




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
COMMAND =  CLAMDIR + "/wrappers/uctowrapper.py " + BINDIR + " $DATAFILE $STATUSFILE $OUTPUTDIRECTORY > $OUTPUTDIRECTORY/log"


PROFILES = [
    Profile(
        InputTemplate('untokinput', PlainTextFormat,"Text document", 
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),  
            ChoiceParameter(id='language',name='Language',description='The language this text is in', choices=[('en','English'),('nl','Dutch'),('nl-twitter','Dutch on Twitter'),('fr','French'),('de','German'),('it','Italian'),('fy','Frisian')], required=True),
            StringParameter(id='documentid', name='Document ID', description='Enter a unique identifier for this document (no spaces). Needed only for XML output, will be auto-generated if not specified.'),
            StringParameter(id='author', name='Author', description='The author of the document (optional)'),
            PDFtoTextConverter(id='pdfconv',label='Convert from PDF Document'),
            MSWordConverter(id='mswordconv',label='Convert from MS Word Document'),
            CharEncodingConverter(id='latin1',label='Convert from Latin-1 (iso-8859-1)',charset='iso-8859-1'),
            CharEncodingConverter(id='latin9',label='Convert from Latin-9 (iso-8859-15)',charset='iso-8859-15'),
            extension='txt',
            multi=True,
        ),
        ParameterCondition(xml=True,
        then=OutputTemplate('foliatokoutput', FoLiAXMLFormat, "Tokenised Text Document (FoLiA XML)",
                SetMetaField('tokenisation','ucto'),
                copymetadata=True,
                removeextension='txt',
                extension='xml',
                multi=True,                
             ),
        otherwise=ParameterCondition(verbose=True,
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
                removeextension='txt',
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
                removeextension='txt',
                extension='tok',
                multi=True,
            )
        )
        )
    ),
]

PARAMETERS =  [ 
    ('Tokenisation options', [
        BooleanParameter('xml','FoLiA XML Output','Output FoLiA XML',value=True),
        BooleanParameter('verbose','Verbose tokeniser output','Outputs token types per token, one token per line',paramflag='-V',forbid=['sentenceperline','xml'] ),
        BooleanParameter('sentenceperline','Sentence per line','Output each sentence on a single line. Does not work in verbose or XML mode.', paramflag='-n', forbid=['verbose','xml']),    
        BooleanParameter('lowercase','Lowercase','Convert text to lowercase',forbid=['uppercase', 'xml'], paramflag='-l'),
        BooleanParameter('uppercase','Uppercase','Convert text to uppercase',forbid=['lowercase', 'xml'], paramflag='-u'),        
    ]),
]

