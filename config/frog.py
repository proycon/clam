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
from os import uname


REQUIRE_VERSION = 0.5

#============== General meta configuration =================
SYSTEM_ID = "frog"
SYSTEM_NAME = "Frog"
SYSTEM_DESCRIPTION = "Frog is a suite containing a tokeniser, PoS-tagger, lemmatiser, morphological analyser, and dependency parser for Dutch, developed at Tilburg University. It is the successor of Tadpole."

# ================ Root directory for CLAM ===============
host = uname()[1]
if host == 'aurora': #proycon's laptop
    CLAMDIR = "/home/proycon/work/demo/clam"
    ROOT = "/home/proycon/work/frog.clam/"
    PORT = 8000
    #URLPREFIX = 'frog'
else:
    raise Exception("Help! I don't know where I'm running from! Configure me!")


#=========== Definition of users and passwords =====================

#Users and passwords

USERS = None #Enable this instead if you want no authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 



#The system command (Use the variables $STATUSFILE $DATAFILE $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY $USERNAME)
COMMAND = CLAMDIR +  "/wrappers/frogwrapper.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY > $OUTPUTDIRECTORY/log"


PROFILES = [
    Profile(
        InputTemplate('maininput', PlainTextFormat,"Text document", 
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),  
            StringParameter(id='author', name='Author', description='The author of the document (optional)'),
            CharEncodingConverter(id='latin1',label='Convert from Latin-1 (iso-8859-1)',charset='iso-8859-1'),
            CharEncodingConverter(id='latin9',label='Convert from Latin-9 (iso-8859-15)',charset='iso-8859-15'),
            multi=True,
        ),
        OutputTemplate('mainoutput', TadpoleFormat,"Tadpole Columned Output Format", 
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
            extension='.frog.out',
            copymetadata=True,
            multi=True,
        ),        
    )
]

PARAMETERS =  [ 
    ('Skip Components', [
        ChoiceParameter('skip', 'Skip Components','Are there any components you want to skip? Skipping the parser speeds up the process considerably.',paramflag='--skip=',choices=[('t','Tokeniser'),('m','Multi-Word Detector'),('p','Parser')], multi=True ),        
    ]), 
]
