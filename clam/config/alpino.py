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

REQUIRE_VERSION = 0.9

SYSTEM_ID = "alpino"
SYSTEM_NAME = "Alpino"
SYSTEM_DESCRIPTION = 'Alpino is a dependency parser for dutch'

#Root directory for CLAM
ROOT = path[0] + "/../alpino.clam/"
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
        ROOT = "/scratch2/www/webservices-lst/live/writable/alpino/"
        HOST = "webservices-lst.science.ru.nl"
        PORT = 80    
    else:
        #test environment
        CLAMDIR = "/scratch2/www/webservices-lst/test/repo/clam"
        ROOT = "/scratch2/www/webservices-lst/test/writable/alpino/"
        HOST = "webservices-lst.science.ru.nl"
        PORT = 81        
    URLPREFIX = "alpino"
    BINDIR = "/vol/customopt/uvt-ru/bin/"    
    USERS_MYSQL = {
        'host': 'mysql-clamopener.science.ru.nl', 
        'user': 'clamopener',        
        'password': D(open(environ['CLAMOPENER_KEYFILE']).read().strip()),
        'database': 'clamopener',
        'table': 'clamusers_clamusers'
    }
    REALM = "WEBSERVICES-LST"
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
COMMAND =  CLAMDIR + "/wrappers/alpinowrapper.py " + BINDIR + " $DATAFILE $STATUSFILE $OUTPUTDIRECTORY > $OUTPUTDIRECTORY/log"


PROFILES = [
    Profile(
        InputTemplate('untokinput', PlainTextFormat,"Text document", 
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),  
            extension='txt',
            multi=True,
        ),
        OutputTemplate('alpinoxml',AlpinoXML,"Alpino XML",
            removeextension='txt',
            extension='xml',
            multi=True,                
        )

    ),
]

PARAMETERS = []
