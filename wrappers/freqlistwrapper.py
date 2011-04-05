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

#import CLAM-specific modules. The CLAM API makes a lot of stuff easily accessible.
import clam.common.data
import clam.common.status



#this script takes three arguments from CLAM: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY  (as configured at COMMAND= in the service configuration file)
datafile = sys.argv[1]
statusfile = sys.argv[2]
outputdir = sys.argv[3]

#Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml))
clamdata = clam.common.data.getclamdata(datafile)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

clam.common.status.write(statusfile, "Starting...")

#SOME EXAMPLES (uncomment and adapt what you need)
    
#-- Iterate over all input files? -- 

#for inputfile in clamdata.input
#   inputtemplate = inputfile.metadata.inputtemplate
#   inputfilepath = str(inputfile)
#   encoding = inputfile.metadata['encoding'] #Example showing how to obtain metadata parameters

#-- Grab a specific input file? (by input template) -- 
inputfile = clamdata.inputfile('tokinput')
inputfilepath = str(inputfile) #full path
filename = os.path.basename(inputfilepath) #filename only
outputfilepath = outputdir + '/' + filename + '.freqlist'

#-- Invoke your actual system? --
os.system('cat ' + inputfilepath + ' | tr " " "\n" | sort | uniq -c | sort -r > ' + outputfilepath);


#A nice status message to indicate we're done
clam.common.status.write(statusfile, "Done",100) # status update

sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
