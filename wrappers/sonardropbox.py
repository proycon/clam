#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Wrapper script Template --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

#This is a test wrapper, meant to illustrate how easy it is to set
#up a wrapper script for your system using Python and the CLAM Client API.
#We make use of the XML configuration file that CLAM outputs, rather than 
#passing all parameters on the command line.

#This script will be called by CLAM and will run with the current working directory set to the specified project directory

#import some general python modules:
import sys
import os
import codecs
import re
import string
import shutil
import glob

#import CLAM-specific modules. The CLAM API makes a lot of stuff easily accessible.
import clam.common.data
import clam.common.status

RECIPIENTS = ['reynaert@uvt.nl','proycon@anaproy.nl']

#this script takes three arguments from CLAM: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY  (as configured at COMMAND= in the service configuration file)
datafile = sys.argv[1]
statusfile = sys.argv[2]
outputdir = sys.argv[3]
submissiondir = sys.argv[4]

#Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml))
clamdata = clam.common.data.getclamdata(datafile)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

clam.common.status.write(statusfile, "Processing your submission...")

#SOME EXAMPLES (uncomment and adapt what you need)
    
#-- Iterate over all input files? -- 


email = clamdata['email']
#sanity check (prevent command line injection):
expmail = re.compile(r"(?:^|\s)[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)",re.IGNORECASE)
if not expmail.match(email):
    print >>sys.stderr,"Invalid e-mail address: " + email
    sys.exit(2)



submissionid = 0
for d in glob.glob(submissiondir+'/*'):
        print >>sys.stderr,d
        if os.path.isdir(d) and os.path.basename(d).strip('/').isdigit():
            if int(os.path.basename(d).strip('/')) > submissionid:
                submissionid = int(os.path.basename(d).strip('/'))
print >>sys.stderr,"Submission ID: ", submissionid
submissionid = str(submissionid + 1)

license = clamdata['licentie']
if license != 'NL' and license != 'B':
    print >>sys.stderr,"Geen licentie gekozen! " + license
    sys.exit(2)    

if submissiondir[-1] != '/': submissiondir += '/'
try:
    os.mkdir(submissiondir)
except:
    pass
submissiondir = submissiondir + submissionid + '/'


os.mkdir(submissiondir)

flog = codecs.open(outputdir + '/log','w','utf-8')
if clamdata['geslacht'] == 'm':
    flog.write('Geachte Heer ' + clamdata['naam'] + '\n\n')
elif clamdata['geslacht'] == 'v':
    flog.write('Geachte Mevrouw ' + clamdata['naam'] + '\n\n')
else:
    flog.write('Geachte Heer/Mevrouw ' + clamdata['naam'] + '\n\n')

flog.write('SoNaR dankt u van harte voor uw bijdrage aan het Referentiecorpus van het hedendaags geschreven Nederlands!\n\n')
flog.write('U heeft de volgende bestanden gedoneerd:\n')

inputdir = None
for inputfile in clamdata.input:    
    inputfilepath = str(inputfile)  
    inputdir  = os.path.dirname(inputfilepath)
    filename = os.path.basename(inputfilepath)
    clam.common.status.write(statusfile, "Processing " + filename)
    shutil.move(inputfilepath, submissiondir + filename)
    flog.write('\t- ' + filename + '\n')


shutil.move(outputdir + '/.log.METADATA', submissiondir + 'metadata.xml')

flog.write('\n')
flog.write('De volgende overeenkomst is hierop van toepassing:\n\n')
if license == 'NL':
    flog.write(u'De eigenaar van de ingestuurde documenten geeft hierbij toestemming aan de Nederlandse Taalunie (NTU) om zijn/haar documenten te (laten) gebruiken ten behoeve van het Stevin Nederlandstalig Referentie Corpus (SoNaR) dat op dit moment ontwikkeld wordt.\n\nSoNaR wordt een databank met minimaal 500 miljoen hedendaagse Nederlandse woorden lopende tekst die als algemene referentie kan dienen voor allerlei onderzoek naar taal en taalgebruik en voor onderzoek op het gebied van de taal- en spraaktechnologie. Bij het verzamelen van teksten gaat speciale aandacht uit naar taalgebruik in nieuwe media, zoals sms-berichten, e-mail, en chats. De inhoud van de ingestuurde documenten zal in de eerste plaats gebruikt worden om de databank verder te ontwikkelen en aan te vullen. Verder kunnen (delen van) de ingestuurde documenten in SoNaR worden opgenomen om te illustreren op welke manier en in welke context bepaalde woorden gebruikt worden.\n\nIn dit verband zal uitsluitend de inhoud van het ingestuurde document worden gebruikt. Persoonsgegevens zullen niet worden gebruikt of op enigerlei wijze openbaar gemaakt worden.\n\nDe deelnemer verleent de NTU hierbij, en de NTU accepteert, het recht om (een deel van) de ingestuurde documenten te gebruiken ten behoeve van de ontwikkeling van SoNaR en het recht om (een deel van) de ingestuurde documenten in SoNaR op te nemen en als onderdeel van SoNaR te verveelvoudigen, openbaar te maken, te hergebruiken en te exploiteren, waaronder begrepen a) het recht (sub)licenties aan derden te verlenen voor het gebruik van SoNaR voor onderzoek en onderwijs b) het verwerken en/of incorporeren van SoNaR in andere producten, zoals corpora en corpus query systems, en c) het recht sublicenties aan derden te verlenen voor het gebruiken van SoNaR voor de ontwikkeling van taal- en/of spraaktechnologische eindproducten en het exploiteren van deze nieuwe producten voor commerciële of niet-commerciële doeleinden.\n\nOp deze overeenkomst, welke als wettelijk bewijs geldt, is het Nederlandse recht van toepassing. Geschillen die voortvloeien uit of verband houden met deze overeenkomst zullen bij uitsluiting voor worden gelegd aan een bevoegde Nederlandse rechtbank.')
elif license == 'B':    
    flog.write(u'De eigenaar van de ingestuurde documenten geeft hierbij toestemming aan de Nederlandse Taalunie (NTU) om zijn/haar documenten te (laten) gebruiken ten behoeve van het Stevin Nederlandstalig Referentie Corpus (SoNaR) dat op dit moment ontwikkeld wordt.\n\nSoNaR wordt een databank met minimaal 500 miljoen hedendaagse Nederlandse woorden lopende tekst die als algemene referentie kan dienen voor allerlei onderzoek naar taal en taalgebruik en voor onderzoek op het gebied van de taal- en spraaktechnologie. Bij het verzamelen van teksten gaat speciale aandacht uit naar taalgebruik in nieuwe media, zoals sms-berichten, e-mail, en chats. De inhoud van de ingestuurde documenten zal in de eerste plaats gebruikt worden om de databank verder te ontwikkelen en aan te vullen. Verder kunnen (delen van) de ingestuurde documenten in SoNaR worden opgenomen om te illustreren op welke manier en in welke context bepaalde woorden gebruikt worden.\n\nIn dit verband zal uitsluitend de inhoud van het ingestuurde document worden gebruikt. Persoonsgegevens zullen niet worden gebruikt of op enigerlei wijze openbaar gemaakt worden.\n\nDe deelnemer verleent de NTU hierbij, en de NTU accepteert, het recht om (een deel van) de ingestuurde documenten te gebruiken ten behoeve van de ontwikkeling van SoNaR en het recht om (een deel van) de ingestuurde documenten in SoNaR op te nemen en als onderdeel van SoNaR te verveelvoudigen, openbaar te maken, te hergebruiken en te exploiteren, waaronder begrepen a) het recht (sub)licenties aan derden te verlenen voor het gebruik van SoNaR voor onderzoek en onderwijs b) het verwerken en/of incorporeren van SoNaR in andere producten, zoals corpora en corpus query systems, en c) het recht sublicenties aan derden te verlenen voor het gebruiken van SoNaR voor de ontwikkeling van taal- en/of spraaktechnologische eindproducten en het exploiteren van deze nieuwe producten voor commerciële of niet-commerciële doeleinden.\n\nOp deze overeenkomst, welke als wettelijk bewijs geldt, is het Belgisch recht van toepassing. Geschillen die voortvloeien uit of verband houden met deze overeenkomst zullen bij uitsluiting voor worden gelegd aan een bevoegde Belgische rechtbank.')

#flog.write('De volgende overeenkomst is hierop van toepassing:\n\n')

flog.write('Met vriendelijke groet,\n\tDr. Martin Reynaert\nTiCC\n In naam van de SoNaR Administratie\n\n')

flog.write('[ID: ' + submissionid + ']\n')

flog.close()

if RECIPIENTS:
    cc = ','.join(RECIPIENTS)
else:
    cc = ""


os.system('mail "' + email + '" -s "SoNaR donatie" ' + cc + ' < ' + outputdir + '/log')

shutil.move(outputdir + '/log', submissiondir + 'log')

#A nice status message to indicate we're done
clam.common.status.write(statusfile, "Done",100) # status update

sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
