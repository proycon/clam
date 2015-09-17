#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Service Configuration File --
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
from os import uname
import sys

REQUIRE_VERSION = 0.7

# ======== GENERAL INFORMATION ===========

# General information concerning your system.


#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "sonardropbox"

#System name, the way the system is presented to the world
SYSTEM_NAME = "SoNaR Tekstdonatie"

#An informative description for this system (this should be fairly short, about one paragraph, and may not contain HTML)
SYSTEM_DESCRIPTION = "Met dit systeem kunt u Nederlandstalige teksten doneren ten bate van het SoNaR corpus."

# ======== LOCATION ===========

#The root directory for CLAM, all project files, (input & output) and
#pre-installed corpora will be stored here. Set to an absolute path:
host = uname()[1]
if host == 'aurora' or host == 'roma': #proycon's laptop/server
    ROOT = "/tmp/clam.projects/"
    SUBMISSIONDIR = ROOT + "submissions/"
    CLAMDIR = "/home/proycon/work/clam"
    PORT= 8080
else:
    #Assuming ILK server
    CLAMDIR = "/var/www/clam"
    ROOT = "/var/www/clamdata/sonardropbox/"
    HOST = 'webservices.ticc.uvt.nl'
    PORT = 80
    URLPREFIX = 'sonar'
    WEBSERVICEGHOST = 'ws'
    BINDIR = '/var/www/bin/'
    SUBMISSIONDIR = "/var/www/clamdata/sonardropbox/submissions/"


#The hostname of the system. Will be automatically determined if not set. (If you start clam with the built-in webserver, you can override this with -H)
#Users *must* make use of this hostname and no other (even if it points to the same IP) for the web application to work.
#HOST = 'localhost'

#If the webservice runs in another webserver (e.g. apache, nginx, lighttpd), and it 
#doesn't run at the root of the server, you can specify a URL prefix here:
#URLPREFIX = "/myservice/"

#The location of where CLAM is installed (will be determined automatically if not set)
#CLAMDIR = "/path/to/clam"

# ======== AUTHENTICATION & SECURITY ===========

#Users and passwords

#set security realm, a required component for hashing passwords (will default to SYSTEM_ID if not set)
#REALM = SYSTEM_ID 

USERS = None #no user authentication/security (this is not recommended for production environments!)

#If you want to enable user-based security, you can define a dictionary
#of users and (hashed) passwords here. The actual authentication will proceed
#as HTTP Digest Authentication. Although being a convenient shortcut,
#using pwhash and plaintext password in this code is not secure!!

#USERS = { user1': '4f8dh8337e2a5a83734b','user2': pwhash('username', REALM, 'secret') }

#Amount of free memory required prior to starting a new process (in MB!), Free Memory + Cached (without swap!). Set to 0 to disable this check (not recommended)
#REQUIREMEMORY = 10

#Maximum load average at which processes are still started (first number reported by 'uptime'). Set to 0 to disable this check (not recommended)
#MAXLOADAVG = 1.0

#Minimum amount of free diskspace in MB. Set to 0 to disable this check (not recommended)
#DISK = '/dev/sda1' #set this to the disk where ROOT is on
#MINDISKSPACE = 10


# ======== WEB-APPLICATION STYLING =============

#Choose a style (has to be defined as a CSS file in style/ ). You can copy, rename and adapt it to make your own style
STYLE = 'classic'

# ======== ENABLED FORMATS ===========

#Here you can specify an extra formats module
CUSTOM_FORMATS_MODULE = None

# ======== PREINSTALLED DATA ===========

#INPUTSOURCES = [
#    InputSource(id='sampledocs',label='Sample texts',path=ROOT+'/inputsources/sampledata',defaultmetadata=PlainTextFormat(None, encoding='utf-8') ),
#]

# ======== PROFILE DEFINITIONS ===========
output = OutputTemplate('log',PlainTextFormat,'Submission log',
    SetMetaField('encoding','utf-8'),
    ParameterMetaField('naam','naam'),
    ParameterMetaField('voornaam','naam'),
    ParameterMetaField('email','email'),
    #ParameterMetaField('adres','adres'),
    #ParameterMetaField('postcode','postcode'),
    #ParameterMetaField('woonplaats','woonplaats'),
    ParameterMetaField('land','land'),
    ParameterMetaField('categories','naam'),
    ParameterMetaField('geslacht','geslacht'),
    ParameterMetaField('leeftijd','leeftijd'),
    ParameterMetaField('opleiding','opleiding'),
    ParameterMetaField('moedertaal','moedertaal'),
    ParameterMetaField('registreernaam','registreernaam'),
    ParameterMetaField('anoniem','anoniem'),
    ParameterMetaField('licentie','licentie'),
    filename='log',
    unique=True,
)


PROFILES = [ 
    Profile(
        InputTemplate('archive', ZIPFormat,"ZIP Archief",  
            extension='.zip',
            multi=True #set unique=True if the user may only upload a file for this input template once. Set multi=True if you the user may upload multiple of such files
        ),
        #------------------------------------------------------------------------------------------------------------------------
        output
    ) ,
    Profile(
        InputTemplate('plaintext', PlainTextFormat,"Platte Tekst",  
            ChoiceParameter(id='encoding',name='Encoding',description='The character encoding of the file', choices=[('utf-8','Unicode (UTF-8)'),('iso-8859-1','Latin1 (iso-8859-1)'),('iso-8859-15','Latin9 (iso-8859-15)'),('cp1250','CP1250')], value='utf-8'),
            extension='.txt',
            multi=True #set unique=True if the user may only upload a file for this input template once. Set multi=True if you the user may upload multiple of such files
        ),
        #------------------------------------------------------------------------------------------------------------------------
        output
    ) ,
    Profile(
        InputTemplate('msword', MSWordFormat,"Microsoft Word document",  
            extension='.doc',
            multi=True #set unique=True if the user may only upload a file for this input template once. Set multi=True if you the user may upload multiple of such files
        ),
        #------------------------------------------------------------------------------------------------------------------------
        output
    ),
    Profile(
        InputTemplate('opendocument', OpenDocumentTextFormat,"OpenDocument Text (odt)",  
            extension='.odt',
            multi=True #set unique=True if the user may only upload a file for this input template once. Set multi=True if you the user may upload multiple of such files
        ),
        #------------------------------------------------------------------------------------------------------------------------
        output

    ),
    Profile(
        InputTemplate('pdf', PDFFormat,"PDF",  
            extension='.pdf',
            multi=True #set unique=True if the user may only upload a file for this input template once. Set multi=True if you the user may upload multiple of such files
        ),
        #------------------------------------------------------------------------------------------------------------------------
        output
    )         

    
]

# ======== COMMAND ===========

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
COMMAND = CLAMDIR + "/wrappers/sonardropbox.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY " + SUBMISSIONDIR

# ======== PARAMETER DEFINITIONS ===========

#The parameters are subdivided into several groups. In the form of a list of (groupname, parameters) tuples. The parameters are a list of instances from common/parameters.py

PARAMETERS =  [ 
    ('Persoonlijke gegevens (ter administratie)', [ 
        StringParameter(id='naam',name='Naam',description='Alleen indien u verderop aanvinkt dat u als auteur van de door u gedoneerde tekst(en) in het corpus bekend wil staan, wordt uw naam in het corpus opgenomen!', required=True),
        StringParameter(id='voornaam',name='Voornaam'),
        StringParameter(id='email',name='E-mail adres',description='Enkel ter administratie. Wordt in geen geval in het corpus opgenomen!' ,required=True),
        #StringParameter(id='adres',name='Straat en huisnummer', description='Enkel ter administratie. Wordt in geen geval in het corpus opgenomen!',required=True),
        #StringParameter(id='postcode',name='Postcode', description='Enkel ter administratie. Wordt in geen geval in het corpus opgenomen!',required=True),
        #StringParameter(id='woonplaats',name='Woonplaats', description='Enkel ter administratie. Wordt in geen geval in het corpus opgenomen!',required=True),
        ChoiceParameter(id='land',name='Land', description='We registreren in het corpus of het Nederlandse dan wel Vlaamse teksten betreft.',choices=[('B',u'België'),('NL','Nederland')],required=True),
    ]),
    ('Tekstsoort',[
        ChoiceParameter(id='categories',name=u'Tekstcategorieën',description='',choices=
            [
                ('WR-P-P-B','Boeken'),
                ('WR-P-P-C','Brochures'),
                ('WR-U-E-A','Chats'),
                ('WR-P-P-O','Columns'),
                ('WR-P-P-D','Digitale nieuwsbrieven'),
                ('WR-P-E-B','E-books (Elektronische boeken)'),
                ('WR-P-E-C','E-magazines (Digitale tijdschriften)'),
                ('WR-U-E-B','E-mails'),
                ('WR-P-P-P','Gedichten'),
                ('WR-P-P-M','Gepubliceerde scripties'),
                ('WR-P-P-E','Gidsen en handleidingen (Bijv. gebruikershandleidingen, instructies)'),
                ('WR-P-E-A','Internetfora'),
                ('WR-P-E-E','Nieuwsbrieven'),
                ('WR-P-E-G','Ondertitels'),
                ('WS-U-E-C','Oraties en redes'),
                ('WR-P-E-F','Persberichten'),
                ('WR-P-P-K','Rapporten'),
                ('WR-P-P-A','Samenvattingen en abstracts'),
                ('WR-U-P-A','Scripties (Bachelor- en Masterscripties)'),
                ('WR-U-E-D','SMS'),
                ('WS-U-E-B','Speeches en toespraken'),
                ('WR-P-P-L','Surveys (Rapporten van grotere onderzoeken, gepubliceerd in boekvorm)'),
                ('WR-P-E-L','Tweets'),
                ('WR-P-E-I','Websites'),
                ('WR-U-E-E','Werkstukken, essays, papers en andere opdrachten van studenten en scholieren'),
            ], multi=True)
    ]),
    ('Extra gegevens ten behoeve van wetenschappelijk onderzoek', [
        ChoiceParameter(id='geslacht',name='Geslacht', description='Vul dit vrijblijvend in indien u wilt bijdragen aan taalkundig wetenschappelijk onderzoek. Dit wordt in het corpus opgenomen.',choices=[('na','Geen antwoord (anoniem)'),('m','Man'),('v','Vrouw')],required=True),
        ChoiceParameter(id='leeftijd',name='Leeftijd', description='Vul dit vrijblijvend in indien u wilt bijdragen aan taalkundig wetenschappelijk onderzoek. Dit wordt in het corpus opgenomen.',choices=[('na','Geen antwoord (anoniem)'),('15-20','15 tot 20'),('20-30','20 tot 30'),('30-40','30 tot 40'),('40-50','40 tot 50'),('50-60','50 tot 60'),('60-70','60 tot 70'), ('70-80','70 tot 80'),('80-90','80 tot 90'),('90-100','90 t/m 100')],required=True),
        ChoiceParameter(id='opleiding',name='Opleiding', description='Vul dit vrijblijvend in indien u wilt bijdragen aan taalkundig wetenschappelijk onderzoek. Dit wordt in het corpus opgenomen.',choices=[('na','Geen antwoord (anoniem)'),('academisch','Academisch'),('hogeronderwijs','Hoger Onderwijs'),('middelbaaronderwijs','Middelbaar Onderwijs'),('lageronderwijs','Lager Onderwijs')    ],required=True),
        ChoiceParameter(id='moedertaal',name='Moedertaal', description='Vul dit vrijblijvend in indien u wilt bijdragen aan taalkundig wetenschappelijk onderzoek. Dit wordt in het corpus opgenomen.',choices=[('na','Geen antwoord (anoniem)'),('nederlands','Nederlands'),('niet-nederlands','Niet-Nederlands')],required=True),
    ]),
    ('Rechtspositie',[
        BooleanParameter(id='registreernaam',name='Ik wens in het corpus bij naam erkend te worden als de auteur van de hierbij door mij gedoneerde teksten'),
        BooleanParameter(id='anoniem',name='Ik verkies anoniem te blijven', description='Vult u a.u.b. toch alle bovenstaande gegevens in, maar deze zullen niet in het corpus worden opgenomen'),
        ChoiceParameter(id='licentie',name='Ik accepteer mijn donatie onder de voorwaarden van de volgende overeenkomst',description='De volledige tekst van de overeenkomst is bovenaan deze pagina terug te vinden en wordt u per e-mail toegestuurd', choices=[('geen','geen acceptatie (Uw donatie is ongeldig!)'),('NL','Nederlandse overeenkomst'),('B','Belgische Overeenkomst')],required=True ),
    ])    
]




# ======== DISPATCHING (ADVANCED! YOU CAN SAFELY SKIP THIS!) ========

#The dispatcher to use (defaults to clamdispatcher.py), you almost never want to change this
#DISPATCHER = 'clamdispatcher.py' 

#Run background process on a remote host? Then set the following (leave the lambda in):
#REMOTEHOST = lambda: return 'some.remote.host'
#REMOTEUSER = 'username'

#For this to work, the user under which CLAM runs must have (passwordless) ssh access (use ssh keys) to the remote host using the specified username (ssh REMOTEUSER@REMOTEHOST)
#Moreover, both systems must have access to the same filesystem (ROOT) under the same mountpoint.
