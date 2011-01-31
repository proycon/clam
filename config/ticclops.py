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
from clam.common.converters import *
from clam.common.viewers import *
from clam.common.data import *
from clam.common.digestauth import pwhash
import sys
REQUIRE_VERSION = 0.5

#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "ticclops"

#System name, the way the system is presented to the world
SYSTEM_NAME = "TICCLops"

#An informative description for this system:
SYSTEM_DESCRIPTION = "TICCLops is the online processing system representing TICCL (Text-Induced Corpus Clean-up) developed within the CLARIN-NL framework."

#The root directory for CLAM, all project files, (input & output) and
#pre-installed corpora will be stored here. Set to an absolute path:
ROOT = "/exp2/ticclops2/"

#The URL of the system
PORT = 1988 
HOST = 'localhost'
#URL = "http://localhost:" + str(PORT)



#Users and passwords
USERS = None #no user authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 
#Do you want all projects to be public to all users? Otherwise projects are 
#private and only open to their owners and users explictly granted access.
PROJECTS_PUBLIC = False

#Amount of free memory required prior to starting a new process (in MB!), Free Memory + Cached (without swap!)
REQUIREMEMORY = 10

#Maximum load average at which processes are still started (first number reported by 'uptime')
MAXLOADAVG = 1.0


# ======== WEB-APPLICATION STYLING =============

#Choose a style (has to be defined as a CSS file in style/ )
STYLE = 'classic'

# ======== ENABLED FORMATS ===========

#Here you can specify an extra formats module
CUSTOM_FORMATS_MODULE = None



PROFILES = [
    Profile(
        InputTemplate('textinput', PlainTextFormat, 'Plain-Text Input',
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='iso-8859-1'),  
            StaticParameter(id='language',name='Language',description='The language of the text', value='nl'),  
            #ChoiceParameter(id='language',name='Language',description='The language this text is in', choices=[('en','English'),('nl','Dutch'),('fr','French'),('de','German'),('it','Italian')]),
            CharEncodingConverter(id='utf8',label='Convert from UTF-8',charset='utf-8'),
            MSWordConverter(id='msword',label='Convert from MS Word Document'),
            PDFToTextConverter(id='pdf',label='Convert from PDF Document'),
            extension='.txt',
            multi=True,
        ),
        InputTemplate('lexicon', PlainTextFormat,  'Lexicon',
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='iso-8859-1'),  
            StaticParameter(id='language',name='Language',description='The language of the text', value='nl'),  
            InputSource(id='contemp', label="Contemporary Dutch Lexicon",
                path="/son/KB-TICCL/PRODv4/ARG4.SGDLEX.isolat1.TICCL.v.4.lst",
                metadata=PlainTextFormat(None, encoding='iso-8859-1',language='nl')    
            ),
            InputSource(id='hist', label="Historical Dutch Lexicon",
                path="/son/KB-TICCL/PRODv4/ARG4.SGDLEX.GB1914.isolat1.TICCL.v.4.lst",
                metadata=PlainTextFormat(None, encoding='iso-8859-1',language='nl')    
            ),
            InputSource(id='none', label="Empty lexicon",
                path="/son/KB-TICCL/PRODv2/empty.lst2",
                metadata=PlainTextFormat(None, encoding='iso-8859-1',language='nl')    
            ),
            filename='lexicon',
            unique=True,
        ),
        ParameterCondition(switches_contains='K',
            then=OutputTemplate('shadow', TICCLShadowOutputXML, 'Corrected plain-text Document',
                StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),  
                StaticParameter(id='language',name='Language',description='The language of the text', value='nl'),  
                extension='.shadow.xml',
                removeextensions=['txt'],
                multi=True,
            ),
        ),
        OutputTemplate('varout', TICCLVariantOutputXML, 'Variant Output',
            filename='varout.xml',
            unique=True,
        ),
    ),
    
]

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
#     $CONFFILE        - Filename of the clam.xml file describing the 
#                        system and chosen configuration.
#     $USERNAME        - The username of the currently logged in user
#                        (set to "anonymous" if there is none)
#     $PARAMETERS      - List of chosen parameters, using the specified flags
#
#COMMAND = "/exp2/mvgompel/clam/wrappers/ticclopswrapper.sh $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY $PARAMETERS" 

COMMAND = sys.path[0] +  "/wrappers/ticclopswrapper.pl $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY $STATUSFILE"


#The parameters are subdivided into several group. In the form of a list of (groupname, parameters) tuples. The parameters are a list of instances from common/parameters.py
PARAMETERS = [
    #('Lexicon', [ChoiceParameter('contemp','-l','Choose a Dutch Lexicon','Dutch Lexicon',choices=[('contemp','Contemporary Dutch lexicon'),('hist','Historical/Contemporary Dutch lexicon'),('none','No validated Dutch lexicon')], nospace=True)
    #]),
    ('Focus Word Selection', [
        IntegerParameter('minfrq','-a','Minimum Word Frequency','Integer between zero and ten million',default=0, minvalue=0, maxvalue=10000000),
        IntegerParameter('maxfrq','-b','Maximum Word Frequency','Integer between zero and ten million',default=10000000,minvalue=0, maxvalue=10000000),
        IntegerParameter('minlength','-c','Minimum Word Length','Integer between zero and one hundred',default=0,minvalue=0, maxvalue=100),
        IntegerParameter('maxlength','-d','Maximum Word Length','Integer between zero and one hundred',default=100,minvalue=0, maxvalue=100)
    ]),
    ('Edit/Levenshtein Distance', [
        ChoiceParameter('ld','-e','How many edits?','Search N characters far for variants',choices=[('1','Only 1 edit'),('2','Up to two edits'),('3','Up to three edits')], nospace=True)
    ]),
#('Extension of Input Files',[
        #ChoiceParameter('ext','-f','Extension','Extension of Input files',choices=
#[('xml','xml'),('txt','txt'),('dif','dif')]),
#]),
    #('Basic name for Output Files', [
    #    StringParameter('string','-s','File name','Enter a basic file name')
    #]),
    ('N-best Ranking', [
        ChoiceParameter('top','-t','How many ranked variants?','Return N best-first ranked variants',choices=[('1','First-best Only'),('2','Up to two N-best ranked'),('3','Up to three N-best ranked'),('5','Up to five N-best ranked'),('10','Up to ten N-best ranked'),('20','Up to twenty N-best ranked')], nospace=True)
    ]),
    ('Options', [
        ChoiceParameter('switches','-w', 'Options', 'Which options do you want to set?', choices=[('E', 'Evaluation'), ('C', 'Conversion'), ('K', 'Text Correction')], multi=True)
    ])
]

