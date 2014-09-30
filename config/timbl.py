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

SYSTEM_ID = "timbl"
SYSTEM_NAME = "Timbl"
SYSTEM_DESCRIPTION = "TiMBL is an open source software package implementing several memory-based learning algorithms, among which IB1-IG, an implementation of k-nearest neighbor classification with feature weighting suitable for symbolic feature spaces, and IGTree, a decision-tree approximation of IB1-IG. All implemented algorithms have in common that they store some representation of the training set explicitly in memory. During testing, new cases are classified by extrapolation from the most similar stored cases.\n\nFor the past decade, TiMBL has been mostly used in natural language processing as a machine learning classifier component, but its use extends to virtually any supervised machine learning domain. Due to its particular decision-tree-based implementation, TiMBL is in many cases far more efficient in classification than a standard k-nearest neighbor algorithm would be."

#Root directory for CLAM
ROOT = path[0] + "/../timbl.clam/"
PORT = 8080

#Users and passwords
USERS = None #Enable this instead if you want no authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!!


# ================ Server specific configurations for CLAM ===============
host = uname()[1]
if host == 'galactica' or host == 'roma': #proycon's laptop/server
    CLAMDIR = "/home/proycon/work/clam"
    ROOT = "/home/proycon/work/timbl.clam/"
    PORT = 9001
    BINDIR = "/home/proycon/local/bin/"
elif host == 'applejack': #Nijmegen
    if not 'CLAMTEST' in environ:
        #live production environment/
        CLAMDIR = "/scratch2/www/webservices-lst/live/repo/clam"
        ROOT = "/scratch2/www/webservices-lst/live/writable/timbl/"
        HOST = "webservices-lst.science.ru.nl"
        PORT = 80
    else:
        #test environment
        CLAMDIR = "/scratch2/www/webservices-lst/test/repo/clam"
        ROOT = "/scratch2/www/webservices-lst/test/writable/timbl/"
        HOST = "webservices-lst.science.ru.nl"
        PORT = 81
    URLPREFIX = "timbl"
    BINDIR = "/vol/customopt/uvt-ru/bin/"
    USERS_MYSQL = {
        'host': 'mysql-clamopener.science.ru.nl',
        'user': 'clamopener',
        'password': D(open(environ['CLAMOPENER_KEYFILE']).read().strip()),
        'database': 'clamopener',
        'table': 'clamusers_clamusers'
    }
    REALM = "WEBSERVICES-LST"
    ADMINS = ['proycon','antalb','wstoop']
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
COMMAND =  CLAMDIR + "/wrappers/timblwrapper.py $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY $PARAMETERS > $OUTPUTDIRECTORY/log"


PROFILES = [
    Profile(
        InputTemplate('traindata', PlainTextFormat,"Training data (plain-text, space-separated)",
            ChoiceParameter(id='encoding',name='Encoding',description='The character encoding of the file', choices=[('utf-8','UTF-8 (Unicode)'),('iso-8859-1','ISO-8859-1 (Latin1)'),('iso-8859-15','so-8859-15 (Latin9)'),('ascii','ASCII')]),
            extension='train',
        ),
        InputTemplate('testdata', PlainTextFormat,"Test data (plain-text, space-separated)",
            ChoiceParameter(id='encoding',name='Encoding',description='The character encoding of the file', choices=[('utf-8','UTF-8 (Unicode)'),('iso-8859-1','ISO-8859-1 (Latin1)'),('iso-8859-15','iso-8859-15 (Latin9)'),('ascii','ASCII')]),
            extension='test',
            multi=True,
        ),
        OutputTemplate('out', PlainTextFormat, "Classifier Output",
            CopyMetaField('encoding','traindata.encoding'),
            extension='timblout',
        ),
    ),
]

PARAMETERS =  [
    ('Classifier Options', [
        ChoiceParameter('a','Algorithm', 'Classification Algorithm',choices=[('IB1','IB1'),('IG','IGTree'),('TRIBL','TRIBL'),('IB2','IB2'),('TRIBL2','TRIBL2')], default='IB1', paramflag='-a'),
        IntegerParameter('k','k-Nearest Neighbours', 'k-Nearest Neighbours', default=1, paramflag='-k'),
        ChoiceParameter('w','Weighting', 'Weighting method',choices=[('nw','No weighting'),('gr','GainRatio'),('ig','InfoGain'),('x2','Chi-square'),('sv','Shared Variance'),('sd','Standard Deviation (all features must be numeric)')], default='gr', paramflag='-w'),
        ChoiceParameter('m','Feature metrics', 'Feature metric (for all features)', choices=[('C','Cosine distance (numeric values only)'),('D','Dot product (numeric values only'), ('DC','Dice Coefficient'),('O','weighted Overlap'),('L','Levenshtein distance'),('E', 'Euclidian Distance'),('M','Modified value difference'),('J','Jeffrey Divergence'),('S','Jenson-Shannon Divergence'),('N','Numeric values'),('I','Ignore named values') ], default='O', paramflag='-m'),
        ChoiceParameter('d','Distance weighting', 'Weigh neigbours as a function of their distance', choices=[('Z','Equal weights to all'),( 'ID', 'Inverse Distance'),('IL','Inverse Linear'),('ED:2','Exponential Decay with factor 2')], paramflag='-d'),
        BooleanParameter('s', 'Exemplar Weights', 'Use exemplar weights from the input file', paramflag='-s'),
        BooleanParameter('leaveoneout', 'Leave-one-out', 'Test using leave-one-out instead of test file', paramflag='-t leave_one_out'),
    ]),
    ('Input  Format', [
        ChoiceParameter('F','Input Format','Input format for training and test files',choices=[('Compact','Compact'),('C4.5','C4.5'),('ARFF','ARFF'),('Columns','Columns'),('Tabbed','Tabbed')], default='Columns',paramflag='-F'),
    ]),
    ('Output Options', [
        ChoiceParameter('v', 'Verbosity Level', 'Verbosity level', multi=True, choices=[('o','Show all options set'),('b','Show node/branch count and branching factor'), ('f','Show calculated feature weights'), ('p','Show Value Difference matrices'), ('e', 'Show exact matches'), ('as', 'Show advances statistics (memory consuming)'), ('cm','Show confusion matrix (memory consuming)'),('cs','Show per class statistics (memory consuming)'),('cf','Add confidence to output file'),('di','Add distance to output file'),('db','Add distribution of best matches to output file'),('md','Add matching depth to output file'),('k','Add summary for all k neighbours'),('n','Add nearest neighbours to output file')], paramflag='-v', delimiter='+'),
    ]),
]

