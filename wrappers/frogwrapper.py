#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Wrapper script, demonstrating CLAM Client API --
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

#general python modules:
import sys
import os


#import CLAM-specific modules:
import clam.common.data
import clam.common.status
import clam.common.parameters
import clam.common.formats

os.environ['PYTHONPATH'] = '/var/www/lib/python2.6/site-packages/frog' #Necessary for University of Tilburg servers (change or remove this in your own setup)

#this script takes three arguments: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY
bindir = sys.argv[1]
datafile = sys.argv[2]
statusfile = sys.argv[3]
outputdir = sys.argv[4]

#Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml))
clamdata = clam.common.data.getclamdata(datafile)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

clam.common.status.write(statusfile, "Starting...")

#assemble parameters for Frog:
cmdoptions = ""

if 'skip' in clamdata and clamdata['skip']:
    cmdoptions += ' --skip=' + "".join(clamdata['skip'])    

for i, inputfile in enumerate(clamdata.input):
    clam.common.status.write(statusfile, "Processing " + os.path.basename(str(inputfile)) + "...", round((i/float(len(clamdata.input)))*100))
    if 'sentenceperline' in inputfile.metadata and inputfile.metadata['sentenceperline']:
        cmdoptions += ' -n'                
    if 'docid' in inputfile.metadata and inputfile.metadata['docid']:
        docid = inputfile.metadata['docid']
    else:
        docid = ".".join(os.path.basename(str(inputfile)).split('.')[:-1])                
    docid = docid.replace(' ','-')
    docid = docid.replace('\'','')
    docid = docid.replace('"','')        
    r = os.system(bindir + "frog -c /var/www/etc/frog/frog.cfg " + cmdoptions + " -t " + str(inputfile) + " --id='" + docid + "' -X '" + outputdir + os.path.basename(str(inputfile)) + ".xml' -o '" + outputdir + os.path.basename(str(inputfile)) + ".frog.out'")                    
    if (r != 0):
        clam.common.status.write(statusfile, "Frog returned with an error whilst processing " + os.path.basename(str(inputfile) + ". Aborting"),100)
        sys.exit(1)

clam.common.status.write(statusfile, "Done",100)       

sys.exit(0) #non-zero exit codes indicate an error! 
