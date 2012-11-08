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
from sys import path 
from os import uname, environ
from base64 import b64decode as D

REQUIRE_VERSION = 0.7

#THIS CONFIGURATION IS FOR FROG >= 0.12.10 ! OLDER VERSIONS WON'T WORK WITH IT!

#============== General meta configuration =================
SYSTEM_ID = "frog"
SYSTEM_NAME = "Frog"
SYSTEM_DESCRIPTION = "Frog is a suite containing a tokeniser, Part-of-Speech tagger, lemmatiser, morphological analyser, shallow parser, and dependency parser for Dutch, developed at Tilburg University. It is the successor of Tadpole."




# ================ Server specific configuration for CLAM ===============
host = uname()[1]
if host == 'aurora' or host == 'roma': #proycon's laptop/server
    CLAMDIR = "/home/proycon/work/clam"
    ROOT = "/home/proycon/work/frog.clam/"
    PORT = 9001
    BINDIR = "/usr/local/bin/"
    #URLPREFIX = 'frog'
elif host == 'applejack': #Nijmegen
    CLAMDIR = "/scratch2/www/webservices-lst/live/repo/clam"
    ROOT = "/scratch2/www/webservices-lst/live/writable/frog/"
    HOST = "webservices-lst.science.ru.nl"
    PORT = 80
    URLPREFIX = "frog"
    BINDIR = "/vol/customopt/uvt-ru/bin/"
    USERS_MYSQL = {
        'host': 'mysql-clamopener.science.ru.nl', 
        'user': 'clamopener',        
        'password': D(open(environ['CLAMOPENER_KEYFILE']).read().strip()),
        'database': 'clamopener',
        'table': 'clamusers_clamusers'
    }
elif host == 'echo' or host == 'nomia' or host == 'echo.uvt.nl' or host == 'nomia.uvt.nl': #Tilburg
    #Assuming ILK server
    CLAMDIR = "/var/www/clam"
    ROOT = "/var/www/clamdata/frog/"
    HOST = 'webservices.ticc.uvt.nl'
    PORT = 80
    URLPREFIX = 'frog'
    WEBSERVICEGHOST = 'ws'
    BINDIR = "/var/www/bin/"
else:
    raise Exception("I don't know where I'm running from! Got " + host)
 



#The system command (Use the variables $STATUSFILE $DATAFILE $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY $USERNAME)
COMMAND = CLAMDIR +  "/wrappers/frogwrapper.py " + BINDIR + " $DATAFILE $STATUSFILE $OUTPUTDIRECTORY > $OUTPUTDIRECTORY/log"


PROFILES = [
    Profile(
        InputTemplate('maininput', PlainTextFormat,"Text document", 
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),  
            StringParameter(id='author', name='Author', description='The author of the document (optional)'),
            StringParameter(id='docid', name='Document ID', description='An ID for the document (optional, used with FoLiA XML output)'),
            BooleanParameter(id='sentenceperline', name='One sentence per line?', description='If set, assume that this input file contains exactly one sentence per line'),
            PDFtoTextConverter(id='pdfconv',label='Convert from PDF Document'),
            MSWordConverter(id='mswordconv',label='Convert from MS Word Document'),
            CharEncodingConverter(id='latin1',label='Convert from Latin-1 (iso-8859-1)',charset='iso-8859-1'),
            CharEncodingConverter(id='latin9',label='Convert from Latin-9 (iso-8859-15)',charset='iso-8859-15'),
            multi=True,
            extension='.txt',
        ),
        OutputTemplate('mainoutput', TadpoleFormat,"Frog Columned Output (legacy)",  #named 'mainoutput' for legacy reasons
            SetMetaField('tokenisation','yes'),
            SetMetaField('postagging','yes'),
            SetMetaField('lemmatisation','yes'),
            SetMetaField('morphologicalanalysis','yes'),
            ParameterCondition(skip_contains='m',
                then=SetMetaField('mwudetection','no'),
                otherwise=SetMetaField('mwudetection','yes'), 
            ),                        
            ParameterCondition(skip_contains='p',
                then=SetMetaField('parsing','no'),
                otherwise=SetMetaField('parsing','yes'),
            ),
            removeextensions=['.txt','.xml'],            
            extension='.frog.out',
            copymetadata=True,
            multi=True,
        ),
        OutputTemplate('foliaoutput', FoLiAXMLFormat,"FoLiA Document",
            FoLiAViewer(), 
            removeextensions=['.txt'],
            extension='.xml',
            copymetadata=True,
            multi=True,
        ),        
    ),
    Profile(
        InputTemplate('foliainput', FoLiAXMLFormat,"FoLiA XML document",
            extension='.xml', 
            multi=True,
        ),
        OutputTemplate('mainoutput', TadpoleFormat,"Frog Columned Output (legacy)",  #named 'mainoutput' for legacy reasons
            SetMetaField('tokenisation','yes'),
            SetMetaField('postagging','yes'),
            SetMetaField('lemmatisation','yes'),
            SetMetaField('morphologicalanalysis','yes'),
            ParameterCondition(skip_contains='m',
                then=SetMetaField('mwudetection','no'),
                otherwise=SetMetaField('mwudetection','yes'), 
            ),                        
            ParameterCondition(skip_contains='p',
                then=SetMetaField('parsing','no'),
                otherwise=SetMetaField('parsing','yes'),
            ),            
            removeextensions=['.xml','.txt'],
            extension='.frog.out',
            copymetadata=True,
            multi=True,
        ),
        OutputTemplate('foliaoutput', FoLiAXMLFormat,"FoLiA Document",                    
            FoLiAViewer(),
            extension='.xml', 
            copymetadata=True,
            multi=True,
        ),        
    ),    
    
]

PARAMETERS =  [

    ('Modules', [
        ChoiceParameter('skip', 'Skip modules','Are there any components you want to skip? Skipping components you do not need may speed up the process considerably.',paramflag='--skip=',choices=[('t','Tokeniser'),('m','Multi-Word Detector'),('p','Parser'),('c','Chunker / Shallow parser'),('n','Named Entity Recognition')], multi=True ),        
        #ChoiceParameter('skip', 'Skip Components','Are there any components you want to skip? Skipping the parser speeds up the process considerably.',paramflag='--skip=',choices=[('p','Skip dependency parser'),('n',"Don't skip anything")] ),
    ]),     
]
