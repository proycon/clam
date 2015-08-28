#!/usr/bin/env python3
#-*- coding:utf-8 -*-


###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Settings --
#       by Maarten van Gompel (proycon)
#       http://proycon.github.io/clam/
#       Centre for Language and Speech Technology  / Language Machines
#       Radboud University Nijmegen
#
#       Licensed under GPLv3
#
###############################################################

from __future__ import print_function, unicode_literals, division, absolute_import

from clam.common.parameters import *
from clam.common.formats import *
from clam.common.viewers import *
from clam.common.data import *
from clam.common.converters import *
from clam.common.digestauth import pwhash
import clam
import os
from base64 import b64decode as D

REQUIRE_VERSION = 0.99
CLAMDIR = clam.__path__[0]

SYSTEM_ID = "ucto"
SYSTEM_NAME = "Ucto Tokeniser"
SYSTEM_DESCRIPTION = 'Ucto is a unicode-compliant tokeniser. It takes input in the form of one or more untokenised texts, and subsequently tokenises them. Several languages are supported, but the software is extensible to other languages.'


#Users and passwords
USERS = None #Enable this instead if you want no authentication


# ================ Server specific configuration for CLAM ===============
host = os.uname()[1]
if 'VIRTUAL_ENV' in os.environ and os.path.exists(os.environ['VIRTUAL_ENV'] +'/bin/ucto'):
    # Virtual Environment (LaMachine)
    ROOT = os.environ['VIRTUAL_ENV'] + "/ucto.clam/"
    PORT = 8802
    BINDIR = os.environ['VIRTUAL_ENV'] + '/bin/'

    if host == 'applejack': #configuration for server in Nijmegen
        HOST = "webservices-lst.science.ru.nl"
        URLPREFIX = 'ucto'

        if not 'CLAMTEST' in os.environ:
            ROOT = "/scratch2/www/webservices-lst/live/writable/ucto/"
            if 'CLAMSSL' in os.environ:
                PORT = 443
            else:
                PORT = 80
        else:
            ROOT = "/scratch2/www/webservices-lst/test/writable/ucto/"
            PORT = 81

        USERS_MYSQL = {
            'host': 'mysql-clamopener.science.ru.nl',
            'user': 'clamopener',
            'password': D(open(os.environ['CLAMOPENER_KEYFILE']).read().strip()),
            'database': 'clamopener',
            'table': 'clamusers_clamusers'
        }
        DEBUG = False
        REALM = "WEBSERVICES-LST"
        DIGESTOPAQUE = open(os.environ['CLAM_DIGESTOPAQUEFILE']).read().strip()
        SECRET_KEY = open(os.environ['CLAM_SECRETKEYFILE']).read().strip()
        ADMINS = ['proycon','antalb','wstoop']
elif os.path.exists('/usr/bin/ucto') and os.path.exists("/home/vagrant") and os.getuid() == 998:
    # Virtual Machine (LaMachine)
    ROOT = "/home/vagrant/ucto.clam/"
    PORT = 8802
    BINDIR = '/usr/bin/'
elif os.path.exists('/usr/bin/ucto') and os.getuid() == 0 and os.path.exists('/etc/arch-release'):
    # Docker (LaMachine)
    ROOT = "/root/ucto.clam/"
    PORT = 8802
    BINDIR = '/usr/bin/'
elif host == "hostnameofyoursystem":
    #**** adapt hostname and add custom configuration for your system here ****
    raise NotImplementedError
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

