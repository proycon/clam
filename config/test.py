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
import sys

REQUIRE_VERSION = 0.7

#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "test"

#System name, the way the system is presented to the world
SYSTEM_NAME = "CLAM Test"

#An informative description for this system:
SYSTEM_DESCRIPTION = "This is a test case for CLAM."

#The root directory for CLAM, all project files, (input & output) and
#pre-installed corpora will be stored here. Set to an absolute path:
ROOT = "/tmp/clamtestroot/"

#The URL of the system
#URL = "http://localhost:8080"
PORT= 8080

#Users and passwords
USERS = None #no user authentication
#USERS = { 'admin': pwhash('admin', SYSTEM_ID, 'secret'), 'proycon': pwhash('proycon', SYSTEM_ID, 'secret'), 'antal': pwhash('antal', SYSTEM_ID, 'secret') , 'martin': pwhash('martin', SYSTEM_ID, 'secret') }

#ADMINS = ['admin'] #Define which of the above users are admins
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!!

#Do you want all projects to be public to all users? Otherwise projects are
#private and only open to their owners and users explictly granted access.
PROJECTS_PUBLIC = False

PROFILES = [
    Profile(
        InputTemplate('textinput', PlainTextFormat,"Input text document",
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),
            ChoiceParameter(id='language',name='Language',description='The language the text is in', choices=[('en','English'),('nl','Dutch'),('fr','French')]),
            CharEncodingConverter(id='latin1',label='Convert from Latin-1',charset='iso-8859-1'),
            PDFtoTextConverter(id='pdfconv',label='Convert from PDF Document'),
            MSWordConverter(id='docconv',label='Convert from MS Word Document'),
            extension='.txt',
            multi=True
        ),
        OutputTemplate('statsbydoc',PlainTextFormat,'Document Statistics',
            SetMetaField('encoding','ascii'),
            extension='.stats',
            multi=True
        ),
        OutputTemplate('freqlistbydoc', PlainTextFormat,'Document Frequency list ',
            CopyMetaField('language','textinput.language'),
            CopyMetaField('encoding','textinput.encoding'),
            extension='.freqlist',
            multi=True
        ),
        OutputTemplate('overallstats', PlainTextFormat, 'Overall Statistics',
            SetMetaField('encoding','utf-8'),
            filename='overall.stats',
            unique=True
        ),
        OutputTemplate('overallfreqlist', PlainTextFormat, 'Overall Frequency List',
            SetMetaField('encoding','utf-8'),
            filename='overall.freqlist',
            unique=True
        ),
        ParameterCondition(createlexicon=True,
            then=OutputTemplate('lexicon', PlainTextFormat, 'Lexicon',
                SetMetaField('encoding','utf-8'),
                filename='overall.lexikon',
                unique=True
            )
        )
    )
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
#     $DATAFILE        - Filename of the clam.xml file describing the
#                        system and chosen configuration.
#     $USERNAME        - The username of the currently logged in user
#                        (set to "anonymous" if there is none)
#     $PARAMETERS      - List of chosen parameters, using the specified flags
#
COMMAND = sys.path[0] + "/wrappers/testwrapper.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY $PARAMETERS > $OUTPUTDIRECTORY/log"

#The parameters are subdivided into several group. In the form of a list of (groupname, parameters) tuples. The parameters are a list of instances from common/parameters.py
PARAMETERS =  [
    ('Main', [
        BooleanParameter('boolean','Boolean','To be or not to be? That is the question',paramflag='-b'),
        IntegerParameter('integer','Integer','Integer between zero and ten',minvalue=0, maxvalue=10, paramflag='-i'),
        FloatParameter('float','Float','Float between 0.0 and 1.0',minvalue=0.0, maxvalue=1.0, paramflag='-f'),
        StringParameter('string','String','Enter a word',maxlength=10, paramflag='-s'),
        TextParameter('text','String','Text', paramflag='-t'),
        ChoiceParameter('colourchoice','Choice','Favourite colour',choices=[('red','red'),('green','green'),('blue','blue')], paramflag='-c'),
        ChoiceParameter('cities', 'Visited cities', 'What cities have you visited?', choices=[('amsterdam', 'Amsterdam'), ('ny', 'New York'), ('london', 'London'), ('paris','Paris')], multi=True, paramflag='-C')
    ] )
]

