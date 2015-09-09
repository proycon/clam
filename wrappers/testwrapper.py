#!/usr/bin/env python3
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
import time
import random

#import CLAM-specific modules:
import clam.common.data
import clam.common.status
import clam.common.parameters
import clam.common.formats

#make a shortcut to this function
shellsafe = clam.common.data.shellsafe


#this script takes three arguments: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY
datafile = sys.argv[1]
statusfile = sys.argv[2]
outputdir = sys.argv[3]


#Obtain all data from the CLAM system (stored in $DATAFILE (clam.xml))
clamdata = clam.common.data.getclamdata(datafile)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

clam.common.status.write(statusfile, "Starting...")

bogus_status_pool = ['Counting stars in the sky', 'Playing with big toe', 'Figuring out the meaning of life','Solving global warming','Drinking coffee', 'Holding a staring contest', 'Flirting with other webservers', 'Tying shoelaces','Hysterically running in circles','Juggling memory bits','Plotting to take over the world' ]

#we fake taking a long time to run, with bogus status messages:
for i in range(0,10):
    time.sleep(2)
    bogus_status = random.choice(bogus_status_pool)
    bogus_status_pool.remove(bogus_status)
    clam.common.status.write(statusfile, bogus_status , ((i + 1) * 10)) #last argument represents percentage of completion (0-100)


#Example: output all selected parameters
print("PARAMETERS:")
for parametergroup, parameters in clamdata.parameters:
    for parameter in parameters:
        if parameter.value: #check if it is set
            print("\t" + parameter.name + ": " + str(parameter.value))

#Query a specific parameter:
print("\tYour favourite colour is " + clamdata['colourchoice'])

print("INPUT FILES:")

#Iterate over all inputfiles:
for inputfile in clamdata.input:
    print("\t" + str(inputfile))
    if isinstance(inputfile.metadata, clam.common.formats.PlainTextFormat) or isinstance(inputfile.metadata, clam.common.formats.TokenizedTextFormat): #if the input file is a plain text format
        print("\tProcessing " + str(inputfile))
        clam.common.status.write(statusfile, "Processing " + os.path.basename(str(inputfile)) + "...")

        #invoke 'rev' through the shell to reverse the input, note the use of the shellsafe() function that wraps our input in the specified quotes (second parameter) and makes sure the value doesn't break out of the quoted environment!
        os.system("rev " + shellsafe(str(inputfile),'"') + " > " + shellsafe(outputdir + os.path.basename(str(inputfile)),'"'))
    else:
        print("\tSkipping " + str(inputfile))
        clam.common.status.write(statusfile, "Skipping " + os.path.basename(str(inputfile)) + ", invalid format")

clam.common.status.write(statusfile, "Done",100)

sys.exit(0) #non-zero exit codes indicate an error!

