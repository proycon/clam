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

from parameters import *
from formats import *

SYSTEM_ID = "clamtest"
SYSTEM_NAME = "CLAM Testcase"
SYSTEM_DESCRIPTION = "This is a small test for CLAM"

#Root directory for CLAM
ROOT = "/home/proycon/work/clamtmproot2/"
URL = "http://localhost:8080"

USERS = None

#List of supported Input formats by the system
INPUTFORMATS = [ PlainTextFormat('utf-8',['txt']) ]

#List of delivered Output formats by the system
OUTPUTFORMATS = [ PlainTextFormat('utf-8',['tok']) ]

#The system command (Use the variables $STATUSFILE $CONFFILE $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY)
COMMAND = "/home/proycon/work/clam/tests/testwrapper.py $PARAMETERS > $OUTPUTDIRECTORY/output "


PARAMETERS =  [ 
    ('Main', [ 
        BooleanParameter('boolean','-b','Boolean','To be or not to be? That is the question'),
        IntegerParameter('integer','-i','Integer','Integer between zero and ten',minvalue=0, maxvalue=10),
        FloatParameter('float','-f','Float','Float between 0.0 and 1.0',minvalue=0.0, maxvalue=1.0),
        StringParameter('string','-s','String','Enter a word'),
        TextParameter('text','-t','String','Text'),
        ChoiceParameter('choice','-c','Choice','Favourite colour',choices=[('red','red'),('green','green'),('blue','blue')]),
    ] )
]

