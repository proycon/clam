#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Client for Frog--
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

import sys
import os
import time
import glob
import random
import codecs

sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

from clam.common.client import *
from clam.common.formats import *
import clam.common.status


url = None
noparser = False
tok = False
vtok = False
legtok = False
parameters = {}

files = []
#Process arguments and parameters:
for arg in sys.argv[1:]:
    if arg[0:7] == "http://":
        url = arg
    elif arg[0] == '-':
        if arg == '-P':
            noparser = True
        elif arg == '-t':
            tok = True
        elif arg == '-v':
            vtok = True
        elif arg == '-l':
            legtok = True
    elif os.path.isfile(arg):
        files.append(arg)
    elif os.path.isdir(arg):
        files += [ x for x in glob.glob(arg + '/*') if x[0] != '.' ]
    else:
        print >>sys.stderr, "Unknown argument, or file/directory does not exist: " + arg
        print >>sys.stderr, "Syntax: frogclient.py [OPTIONS] URL TEXTFILES"
        sys.exit(1)

if not url or not files:
    print >>sys.stderr, "Syntax: frogclient.py [OPTIONS] URL TEXTFILES"
    sys.exit(1)    


print "Connecting to server..."

        
#create client, connect to server
clamclient = CLAMClient(url)

print "Creating project..."
   
#this is the name of our project, it consists in part of randomly generated bits (so multiple clients don't use the same project and can run similtaneously)
project = "frogclient" + str(random.getrandbits(64))
clamclient.create(project)


print "Uploading Files..."

for f in files:
    print "\tUploading " + f + " to webservice..."
    clamclient.upload(project, open(f), PlainTextFormat('utf-8') )


print "Starting Frog..."
data = clamclient.start(project, noparser=noparser, tok=tok,vtok=vtok, legtok=legtok) #start the process with the specified parameters
if data.errors:
    print >>sys.stderr,"An error occured: " + data.errormsg
    for parametergroup, paramlist in data.parameters:
        for parameter in paramlist:
            if parameter.error:
                print >>sys.stderr,"Error in parameter " + parameter.id + ": " + parameter.error
    sys.exit(1)


while data.status != clam.common.status.DONE:
    time.sleep(5) #wait 5 seconds before polling status
    data = clamclient.get(project) #get status again
    print "\tFROG IS RUNNING: " + str(data.completion) + '% -- ' + data.statusmessage


print "Frog is done."

#Download output files to current directory
for outputfile in data.output:
    print "\tDownloading " + str(outputfile) + " (" + outputfile.format.name + ") ..."
    clamclient.download(project, outputfile, open(os.path.basename(outputfile.path),'w'))


#delete our project
clamclient.delete(project)

print "All done! Have a nice day!"


