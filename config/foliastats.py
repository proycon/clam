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
from clam.common.viewers import *
from clam.common.data import *
from clam.common.converters import *
from clam.common.digestauth import pwhash
import clam
import os
from base64 import b64decode as D

REQUIRE_VERSION = 0.9
CLAMDIR = clam.__path__[0]

#============== General meta configuration =================
SYSTEM_ID = "foliastats"
SYSTEM_NAME = "FoLiA-stats"
SYSTEM_DESCRIPTION = "N-gram frequency list generation on FoLiA input"


USERS = None

# ================ Server specific configuration for CLAM ===============
host = os.uname()[1]
if 'VIRTUAL_ENV' in os.environ:
    ROOT = os.environ['VIRTUAL_ENV'] + "/foliastats.clam/"
    PORT = 8805
    BINDIR = os.environ['VIRTUAL_ENV'] + '/bin/'

    if host == 'applejack': #configuration for server in Nijmegen
        HOST = "webservices-lst.science.ru.nl"
        URLPREFIX = 'foliastats'

        if not 'CLAMTEST' in os.environ:
            ROOT = "/scratch2/www/webservices-lst/live/writable/foliastats/"
            if 'CLAMSSL' in os.environ:
                PORT = 443
            else:
                PORT = 80
        else:
            ROOT = "/scratch2/www/webservices-lst/test/writable/foliastats/"
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
elif host == 'galactica' or host == 'roma': #proycon's laptop/server
    CLAMDIR = "/home/proycon/work/clam"
    ROOT = "/home/proycon/work/foliastats.clam/"
    PORT = 9001
    BINDIR = "/usr/local/bin/"
    USERS = { 'proycon': pwhash('proycon', SYSTEM_ID, 'secret') }
    #URLPREFIX = 'frog'
elif host == 'echo' or host == 'nomia' or host == 'echo.uvt.nl' or host == 'nomia.uvt.nl': #Tilburg
    #Assuming ILK server
    CLAMDIR = "/var/www/clam"
    ROOT = "/var/www/clamdata/foliastats/"
    HOST = 'webservices.ticc.uvt.nl'
    PORT = 80
    URLPREFIX = 'foliastats'
    WEBSERVICEGHOST = 'ws'
    BINDIR = "/var/www/bin/"
else:
    raise Exception("I don't know where I'm running from! Got " + host)




#The system command (Use the variables $STATUSFILE $DATAFILE $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY $USERNAME)
COMMAND = CLAMDIR +  "/wrappers/foliastats.py " + BINDIR + " $INPUTDIRECTORY $DATAFILE $STATUSFILE $OUTPUTDIRECTORY > $OUTPUTDIRECTORY/log"


PROFILES = [
    Profile(
        InputTemplate('foliainput', FoLiAXMLFormat,"FoLiA XML document",
            extension='.xml',
            multi=True
        ),
        OutputTemplate('wordfreqlist',CSVFormat,"Frequency list",
            SimpleTableViewer(),
            SetMetaField('encoding','utf-8'),
            filename='output.wordfreqlist.tsv',
            unique=True
        ),
        OutputTemplate('lemmafreqlist',CSVFormat,"Lemma Frequency list",
            SimpleTableViewer(),
            SetMetaField('encoding','utf-8'),
            filename='output.lemmafreqlist.tsv',
            unique=True
        ),
        OutputTemplate('lemmaposfreqlist',CSVFormat,"Lemma+PoS Frequency list",
            SimpleTableViewer(),
            SetMetaField('encoding','utf-8'),
            filename='output.lemmaposfreqlist.tsv',
            unique=True
        ),
    )
]

PARAMETERS =  [
    ('Modules', [

        BooleanParameter('lowercase','Lowercase', 'Convert all words to lower case'),
        IntegerParameter('n','N-Gram Count', 'Specify a value for n to count', default=1),
    ]),
]

DISPATCHER_MAXRESMEM = 25000 #25GB
