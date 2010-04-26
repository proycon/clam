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
import clam.common.client
import clam.common.status
import clam.common.parameters
import clam.common.formats

#this script takes three arguments: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY
datafile = sys.argv[1]
statusfile = sys.argv[2]
outputdir = sys.argv[3]


#Obtain all data from the CLAM system (stored in $DATAFILE (clam.xml))
clamdata = common.client.getclamdata(datafile)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

common.status.writestatus(statusfile, "Starting...")

#Example: output all selected parameters
print "PARAMETERS:"
for parametergroup, parameters in clamdata.parameters:
    for parameter in parameters:
        print parameter.name + ": " + str(parameter.value)

#Query a specific parameter:
print "Your favourite colour is " + clamdata['colourchoice'].value

print "INPUT FILES:"    

#Iterate over all inputfiles:
for inputfile in clamdata.input: 
    print str(inputfile)
    if isinstance(inputfile.format, common.formats.PlainTextFormat) or isinstance(inputfile.format, common.formats.TokenizedTextFormat): #if the input file is a plain text format
        common.status.writestatus(statusfile, "Processing " + os.path.basename(inputfile) + "...")
        #invoke 'rev' through the shell to reverse the input
        os.system("rev " + str(inputfile) + " > " + outputdir + os.path.basename(inputfile))

common.status.writestatus(statusfile, "Done")       

sys.exit(0) #non-zero exit codes indicate an error! 

