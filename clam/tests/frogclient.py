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

#We may need to do some path magic in order to find the clam.* imports
sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

#Import the CLAM Client API and other dependencies
from clam.common.client import *
from clam.common.formats import *
import clam.common.status



url = None
skip = []
tok = 'no'
parameters = {}

files = []
#Process arguments and parameters:
for arg in sys.argv[1:]:
    if arg[0:7] == "http://":
        url = arg
    elif arg[0] == '-':
        if arg == '-P':
            skip = ['p']
        elif arg == '-t':
            tok = 'tok'
        elif arg == '-v':
            tok = 'vtok'
    elif os.path.isfile(arg):
        files.append(arg)
    elif os.path.isdir(arg):
        files += [ x for x in glob.glob(arg + '/*') if x[0] != '.' ]
    else:
        print("Unknown argument, or file/directory does not exist: " + arg,file=sys.stderr)
        print("Syntax: frogclient.py [OPTIONS] URL TEXTFILES",file=sys.stderr)
        print >>sys.stderr, "Options: -t\tTokenise only"
        print >>sys.stderr, "         -v\tTokenise only (verbosely)"
        print >>sys.stderr, "         -P\tDisable parser"
        sys.exit(2)

if not url or not files:
    print >>sys.stderr, "Syntax: frogclient.py [OPTIONS] URL TEXTFILES"
    sys.exit(1)


print("Connecting to server...")


#create client, connect to server, url is the full URL to the base of your webservice.
clamclient = CLAMClient(url)

print("Creating project...")

#this is the name of our project, it consists in part of randomly generated bits (so multiple clients don't use the same project and can run similtaneously)

#CLAM works with 'projects', for automated clients it usually suffices to create a temporary project,
#which we explicitly delete when we're all done. Each client obviously needs its own project, so we
#create a project with a random name:
project = "frogclient" + str(random.getrandbits(64))

#Now we call the webservice and create the project
clamclient.create(project)



print("Uploading Files...")


#Upload the files (names were passed on the command line) to the webservice, always indicating
#the format.
for f in files:
    print("\tUploading " + f + " to webservice...")
    #This invokes the actual upload
    clamclient.upload(project, open(f), PlainTextFormat('utf-8') )



print("Starting Frog...")

#Now we invoke the webservice with the parameters that were passed on the command line, effectively
#starting the project. The start() method takes a project name and a set of keyword arguments, the keywords here
#correspond with the parameter IDs defined by your webservice.
data = clamclient.start(project, tok=tok,skip=skip) #start the process with the specified parameters
if data.errors:
    print("An error occured: " + data.errormsg,file=sys.stderr)
    for parametergroup, paramlist in data.parameters:
        for parameter in paramlist:
            if parameter.error:
                print("Error in parameter " + parameter.id + ": " + parameter.error,file=sys.stderr)
    clamclient.delete(project) #delete our project (remember, it was temporary, otherwise clients would leave a mess)
    sys.exit(1)

#If everything went well, the system is now running, we simply wait until it is done and retrieve the status in the meantime
while data.status != clam.common.status.DONE:
    time.sleep(5) #wait 5 seconds before polling status
    data = clamclient.get(project) #get status again
    print("\tFROG IS RUNNING: " + str(data.completion) + '% -- ' + data.statusmessage)

#Good, all is done! We should have some output...
print("Frog is done.")

#Download all output files to current directory
for outputfile in data.output:
    print("\tDownloading " + str(outputfile) + " (" + outputfile.format.name + ") ...")
    f = codecs.open(os.path.basename(str(outputfile)),'w','utf-8')
    for line in outputfile:
        f.write(line)
    f.close()


#delete our project (remember, it was temporary, otherwise clients would leave a mess)
clamclient.delete(project)

print("All done! Have a nice day!")
