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
from clam.common.data import *
from clam.common.converters import *
from clam.common.digestauth import pwhash
import clam
import os
from base64 import b64decode as D

REQUIRE_VERSION = 0.99
CLAMDIR = clam.__path__[0]

SYSTEM_ID = "timbl"
SYSTEM_NAME = "Timbl"
SYSTEM_DESCRIPTION = "TiMBL is an open source software package implementing several memory-based learning algorithms, among which IB1-IG, an implementation of k-nearest neighbor classification with feature weighting suitable for symbolic feature spaces, and IGTree, a decision-tree approximation of IB1-IG. All implemented algorithms have in common that they store some representation of the training set explicitly in memory. During testing, new cases are classified by extrapolation from the most similar stored cases.\n\nFor the past decade, TiMBL has been mostly used in natural language processing as a machine learning classifier component, but its use extends to virtually any supervised machine learning domain. Due to its particular decision-tree-based implementation, TiMBL is in many cases far more efficient in classification than a standard k-nearest neighbor algorithm would be."


#Users and passwords
USERS = None #Enable this instead if you want no authentication
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!!


# ================ Server specific configuration for CLAM ===============
host = os.uname()[1]
if 'VIRTUAL_ENV' in os.environ and os.path.exists(os.environ['VIRTUAL_ENV'] +'/bin/timbl'):
    # Virtual Environment (LaMachine)
    ROOT = os.environ['VIRTUAL_ENV'] + "/timbl.clam/"
    PORT = 8804
    BINDIR = os.environ['VIRTUAL_ENV'] + '/bin/'

    if host == 'applejack': #configuration for server in Nijmegen
        HOST = "webservices-lst.science.ru.nl"
        URLPREFIX = 'timbl'

        if not 'CLAMTEST' in os.environ:
            ROOT = "/scratch2/www/webservices-lst/live/writable/timbl/"
            if 'CLAMSSL' in os.environ:
                PORT = 443
            else:
                PORT = 80
        else:
            ROOT = "/scratch2/www/webservices-lst/test/writable/timbl/"
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
elif os.path.exists('/usr/bin/timbl') and os.path.exists("/home/vagrant") and os.getuid() == 998:
    # Virtual Machine (LaMachine)
    ROOT = "/home/vagrant/timbl.clam/"
    PORT = 8804
    BINDIR = '/usr/bin/'
elif os.path.exists('/usr/bin/timbl') and os.getuid() == 0 and os.path.exists('/etc/arch-release'):
    # Docker (LaMachine)
    ROOT = "/root/timbl.clam/"
    PORT = 8804
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

