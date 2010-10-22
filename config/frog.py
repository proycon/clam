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
from clam.common.digestauth import pwhash
from sys import path
from os import uname


REQUIRE_VERSION = 0.4

#============== General meta configuration =================
SYSTEM_ID = "frog"
SYSTEM_NAME = "Frog"
SYSTEM_DESCRIPTION = "Frog is a suite containing a tokeniser, PoS-tagger, lemmatiser, morphological analyser, and dependency parser for Dutch, developed at Tilburg University. It will be the successor of Tadpole but is still under heavy development. "

# ================ Root directory for CLAM ===============
host = uname()[1]
if host == 'aurora': #proycon's laptop
    CLAMDIR = "/home/proycon/work/clam"
    ROOT = "/home/proycon/work/frog.clam/"
    PORT = 8000
    URLPREFIX = 'frog'
else:
    raise Exception("Help! I don't know where I'm running from! Configure me!")


#=========== Definition of users and passwords =====================

#Users and passwords

USERS = None #Enable this instead if you want no authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!! 


#========== List of supported Input formats by the system =====================
INPUTFORMATS = [ PlainTextFormat('utf-8',['txt']) ]

#========== List of delivered Output formats by the system ====================
OUTPUTFORMATS = [ TadpoleFormat('utf-8',['frogged'], viewer= FrogViewer() ) ]

#========== The system command =======================
#   (Use the variables $STATUSFILE $DATAFILE $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY $USERNAME)
COMMAND = CLAMDIR +  "/wrappers/frogwrapper.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY"


#========== Parameters =======================
PARAMETERS =  [ 
    ('Components', [       
        ChoiceParameter('tok','--tok', 'Tokenise only?', 'Use Frog as a standalone tokeniser?', choices=[('no','No'), ('tok','Yes'),('vtok','Yes (verbosely)')]),
        ChoiceParameter('skip','--skip=', 'Skip modules', 'Modules to disable:', choices=[('t', 'Tokeniser'), ('m', 'Multi-Word-Unit Detection'), ('p', 'Parser')], multi=True),
        BooleanParameter('nopar','--nopar', 'Disable paragraph detection', 'Disables paragraph detection')
    ])

#List of supported Input formats by the system
INPUTFORMATS = [ 
    PlainTextFormat(encoding='utf-8',language='nld', extension='nld.txt'),
    PlainTextFormat(encoding='utf-8',language='deu', extension='deu.txt'),
    PlainTextFormat(encoding='utf-8',language='fra', extension='fra.txt'),
    PlainTextFormat(encoding='utf-8',language='ita', extension='ita.txt'),
    PlainTextFormat(encoding='utf-8',language='spa', extension='spa.txt'),
]

#List of delivered Output formats by the system
OUTPUTFORMATS = [ 
    TadpoleFormat(encoding='utf-8',language='nld', extension='nld.frogged', viewer=FrogViewer() ) ,
    TokenizedTextFormat(encoding='utf-8',language='nld', extension='nld.tok' ),
    TokenizedTextFormat(encoding='utf-8',language='deu', extension='deu.tok' ),
    TokenizedTextFormat(encoding='utf-8',language='fra', extension='fra.tok' ),
    TokenizedTextFormat(encoding='utf-8',language='ita', extension='ita.tok' ),
    TokenizedTextFormat(encoding='utf-8',language='spa', extension='spa.tok' ),
    VerboseTokenizedTextFormat(encoding='utf-8',language='nld', extension='nld.vtok' ),
    VerboseTokenizedTextFormat(encoding='utf-8',language='deu', extension='deu.vtok' ),
    VerboseTokenizedTextFormat(encoding='utf-8',language='fra', extension='fra.vtok' ),
    VerboseTokenizedTextFormat(encoding='utf-8',language='ita', extension='ita.vtok' ),
    VerboseTokenizedTextFormat(encoding='utf-8',language='spa', extension='spa.vtok' ),
]


#Profilers tell what output files will be generated, based on the input files and parameters
PROFILERS = [
     OneToOneProfiler(INPUTFORMATS[0], OUTPUTFORMATS[0], paramcondition=lambda params: (not 'tok' in params or not params['tok']) and (not 'vtok' in params or not params['vtok'])  ),
     OneToOneProfiler(INPUTFORMATS[0], OUTPUTFORMATS[1], paramcondition=lambda params: ('tok' in params and params['tok']) or ('vtok' in params and params['vtok'])  )
]

#The system command (Use the variables $STATUSFILE $DATAFILE $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY $USERNAME)
COMMAND = CLAMDIR +  "/wrappers/frogwrapper.py $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY"

PARAMETERS =  [ 
    ('Configuration', [
        ChoiceParameter('conf','--conf', 'Configuration','Select what configuration to use, most notably; for what language', choices=[('nld','Nederlands'),('eng','English')] )
    ] ),
    ('Components', [
        BooleanParameter('tok','--tok', 'Tokenisation','Produce distinct tokens, separate punctuation'),
        BooleanParameter('pos','--pos', 'PoS-tagging', 'Add Part-of-Speech tags'),
        BooleanParameter('lem','--lem', 'Lemmatisation', 'Resolve lemmas'),
        BooleanParameter('morph','--morph', 'Morphological Analysis', 'Detect morphemes'),
        BooleanParameter('mwu','--mwu', 'Multi-word Unit Detection', 'Detect multi-word units'),
        BooleanParameter('dep','--dep', 'Dependency Parsing', 'Detect syntactic dependencies'),
    ]), 
    ('Output Options', [
        ChoiceParameter('output','--output', 'Output Mode','Select an output mode', choices=[('tok','Output tokenised text only'),('col','Columned output'),('xml','XML Output')],selected='col' )
    ] ),
]
