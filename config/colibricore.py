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
from os import uname, environ
from base64 import b64decode as D

REQUIRE_VERSION = 0.9


#============== General meta configuration =================
SYSTEM_ID = "colibricore"
SYSTEM_NAME = "Colibri Core"
SYSTEM_DESCRIPTION = "A tool for pattern extraction and analysis on corpus data."


USERS = None

# ================ Server specific configuration for CLAM ===============
host = uname()[1]
if host == 'galactica' or host == 'roma': #proycon's laptop/server
    CLAMDIR = "/home/proycon/work/clam"
    ROOT = "/home/proycon/work/colibricore.clam/"
    PORT = 9001
    BINDIR = "/usr/local/bin/"
    USERS = { 'proycon': pwhash('proycon', SYSTEM_ID, 'secret') }
    #URLPREFIX = 'frog'
elif host == 'applejack': #Nijmegen
    if not 'CLAMTEST' in environ:
        CLAMDIR = "/scratch2/www/webservices-lst/live/repo/clam"
        ROOT = "/scratch2/www/webservices-lst/live/writable/colibricore/"
        HOST = "webservices-lst.science.ru.nl"
        PORT = 80
    else:
        CLAMDIR = "/scratch2/www/webservices-lst/test/repo/clam"
        ROOT = "/scratch2/www/webservices-lst/test/writable/colibricore/"
        HOST = "webservices-lst.science.ru.nl"
        PORT = 81
    URLPREFIX = "colibricore"
    BINDIR = "/vol/customopt/uvt-ru/bin/"
    USERS_MYSQL = {
        'host': 'mysql-clamopener.science.ru.nl',
        'user': 'clamopener',
        'password': D(open(environ['CLAMOPENER_KEYFILE']).read().strip()),
        'database': 'clamopener',
        'table': 'clamusers_clamusers'
    }
    DEBUG = False
    REALM = "WEBSERVICES-LST"
    DIGESTOPAQUE = open(environ['CLAM_DIGESTOPAQUEFILE']).read().strip()
    ADMINS = ['proycon','antalb','wstoop']
else:
    raise Exception("I don't know where I'm running from! Got " + host)




#The system command (Use the variables $STATUSFILE $DATAFILE $PARAMETERS $INPUTDIRECTORY $OUTPUTDIRECTORY $USERNAME)
COMMAND = CLAMDIR +  "/wrappers/colibricore.py " + BINDIR + " $DATAFILE $STATUSFILE $OUTPUTDIRECTORY"




PROFILES = [
    Profile(
        InputTemplate('foliainput', FoLiAXMLFormat,"FoLiA XML document",
            extension='.xml',
            multi=True
        ),
        OutputTemplate('corpusfile',BinaryDataFormat,"Colibri Corpus Data",
            removeextensions=['.txt','.xml'],
            extension='.colibri.dat',
            multi=True,
        ),
        OutputTemplate('patternmodel',BinaryDataFormat,"Colibri Pattern Model",
            removeextensions=['.txt','.xml'],
            extension='.colibri.patternmodel',
            multi=True,
        ),
        OutputTemplate('classfile',CSVFormat,"Colibri Class Data",
            removeextensions=['.txt','.xml'],
            extension='.colibri.cls',
            multi=True,
        ),
        ParameterCondition(extract=True,
            then=OutputTemplate('extract',CSVFormat,"Extract Pattern List",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.patterns.csv',
                multi=True
            )
        ),
        ParameterCondition(report=True,
            then=OutputTemplate('report',PlainTextFormat,"Statistical Report",
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.report.txt',
                multi=True
            )
        ),
        ParameterCondition(histogram=True,
            then=OutputTemplate('histogram',CSVFormat,"Histogram",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.histogram.csv',
                multi=True
            )
        ),
        ParameterCondition(reverseindex=True,
            then=OutputTemplate('reverseindex',CSVFormat,"Reverse Index",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.reverseindex.csv',
                multi=True
            )
        ),
        ParameterCondition(cooc=True,
            then=OutputTemplate('cooc',CSVFormat,"Co-occurrence data (absolute)",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.cooc.csv',
                multi=True
            )
        ),
        ParameterCondition(npmi=True,
            then=OutputTemplate('npmi',CSVFormat,"Co-occurrence data (relative)",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.npmi.csv',
                multi=True
            )
        )
    ),
    Profile(
        InputTemplate('textinput_tok', PlainTextFormat,"Plain text input (tokenised)",
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),
            extension='.txt',
            multi=True
        ),
        OutputTemplate('corpusfile',BinaryDataFormat,"Colibri Corpus Data",
            removeextensions=['.txt','.xml'],
            extension='.colibri.dat',
            multi=True,
        ),
        OutputTemplate('patternmodel',BinaryDataFormat,"Colibri Pattern Model",
            removeextensions=['.txt','.xml'],
            extension='.colibri.patternmodel',
            multi=True,
        ),
        OutputTemplate('classfile',CSVFormat,"Colibri Class Data",
            removeextensions=['.txt','.xml'],
            extension='.colibri.cls',
            multi=True,
        ),
        ParameterCondition(extract=True,
            then=OutputTemplate('extract',CSVFormat,"Extract Pattern List",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.patterns.csv',
                multi=True
            )
        ),
        ParameterCondition(report=True,
            then=OutputTemplate('report',PlainTextFormat,"Statistical Report",
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.report.txt',
                multi=True
            )
        ),
        ParameterCondition(histogram=True,
            then=OutputTemplate('histogram',CSVFormat,"Histogram",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.histogram.csv',
                multi=True
            )
        ),
        ParameterCondition(reverseindex=True,
            then=OutputTemplate('reverseindex',CSVFormat,"Reverse Index",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.reverseindex.csv',
                multi=True
            )
        ),
        ParameterCondition(cooc=True,
            then=OutputTemplate('cooc',CSVFormat,"Co-occurrence data (absolute)",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.cooc.csv',
                multi=True
            )
        ),
        ParameterCondition(npmi=True,
            then=OutputTemplate('npmi',CSVFormat,"Co-occurrence data (relative)",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.npmi.csv',
                multi=True
            )
        )
    ),
    Profile(
        InputTemplate('textinput_untok', PlainTextFormat,"Plain text input (untokenised)",
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),
            ChoiceParameter(id='language',name='Language',description='The language of the text', choices=[('en','English'),('nl','Dutch'),('de','German'),('fr','French'),('es','Spanish'),('pt','Portuguese'),('fy','Frysian'),('generic','Other (generic tokeniser)')]),
            BooleanParameter('sentenceperline_input','Input is one sentence per line'),
            BooleanParameter('sentenceperline_output','Output one sentence per line'),
            extension='.txt',
            multi=True
        ),
        OutputTemplate('corpusfile',BinaryDataFormat,"Colibri Corpus Data",
            removeextensions=['.txt','.xml'],
            extension='.colibri.dat',
            multi=True,
        ),
        OutputTemplate('patternmodel',BinaryDataFormat,"Colibri Pattern Model",
            removeextensions=['.txt','.xml'],
            extension='.colibri.patternmodel',
            multi=True,
        ),
        OutputTemplate('classfile',CSVFormat,"Colibri Class Data",
            removeextensions=['.txt','.xml'],
            extension='.colibri.cls',
            multi=True,
        ),
        ParameterCondition(extract=True,
            then=OutputTemplate('extract',CSVFormat,"Extract Pattern List",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.patterns.csv',
                multi=True
            )
        ),
        ParameterCondition(report=True,
            then=OutputTemplate('report',PlainTextFormat,"Statistical Report",
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.report.txt',
                multi=True
            )
        ),
        ParameterCondition(histogram=True,
            then=OutputTemplate('histogram',CSVFormat,"Histogram",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.histogram.csv',
                multi=True
            )
        ),
        ParameterCondition(reverseindex=True,
            then=OutputTemplate('reverseindex',CSVFormat,"Reverse Index",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.reverseindex.csv',
                multi=True
            )
        ),
        ParameterCondition(cooc=True,
            then=OutputTemplate('cooc',CSVFormat,"Co-occurrence data (absolute)",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.cooc.csv',
                multi=True
            )
        ),
        ParameterCondition(npmi=True,
            then=OutputTemplate('npmi',CSVFormat,"Co-occurrence data (relative)",
                SimpleTableViewer(),
                SetMetaField('encoding','utf-8'),
                removeextensions=['.txt','.xml'],
                extension='.npmi.csv',
                multi=True
            )
        )
    ),
]

PARAMETERS =  [
    ('Configuration', [
        BooleanParameter('lowercase','Lowercase', 'Convert all words to lower case'),
        IntegerParameter('mintokens','Occurrence threshold', 'Specify an occurrence threshold, only patterns occurring at least this many times in the corpus will show up in the result', default=2),
        IntegerParameter('minlength','Minimum length', 'Minimum length of n-gram or skipgram', default=1),
        IntegerParameter('maxlength','Maximum length', 'Maximum length of n-gram or skipgram (i.e value of n)', default=5),
        BooleanParameter('skipgrams','Skipgrams', 'Include skipgrams'),
        BooleanParameter('indexing','Indexing', 'Compute an indexed to where in the corpus the pattern is found (memory intensive!)'),
    ]),
    ('Modules (pick at least one)',[
        BooleanParameter('extract','Extract patterns', 'Output a list of all patterns (ngrams, skipgrams) with their counts'),
        BooleanParameter('report','Statistical Report','Output a statistical report of total counts per ngram-group, and coverage information (enable indexing for accurate coverage information)'),
        BooleanParameter('histogram','Histogram', 'Output a histogram of ngram/skipgram occurrence count'),
        BooleanParameter('reverseindex','reverseindex', 'Output a reverse index, for each position in the corpus, the patterns that start on that position are listed'),
        IntegerParameter('cooc','Co-occurrence (absolute)', 'Compute co-occurring patterns (occuring on the same input line in the corpus data) that occur together more than the specified times  (0=disabled)', default=0),
        FloatParameter('npmi','Co-occurrence (relative)', 'Compute co-occurring patterns (occuring on the same input line in the corpus data) that have a normalised mutial information higher than the specified value (-1=disabled)', default=-1),
    ]),
    ('Query',[
        StringParameter('query','Query', 'Query the corpus for the following patterns (rather than all), should be a comma-separated list.'),
    ])
]

DISPATCHER_MAXRESMEM = 25000 #25GB
