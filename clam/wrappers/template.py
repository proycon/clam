#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Wrapper script Template --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#       Centre for Language and Speech Technology
#       Radboud University Nijmegen
#
#       Licensed under GPLv3
#
###############################################################

#This is a template wrapper which you can use a basis for writing your own
#system wrapper script. The system wrapper script is called by CLAM, it's job it
#to call your actual tool.

#This script will be called by CLAM and will run with the current working directory set to the specified project directory

#This wrapper script uses Python and the CLAM Data API.
#We make use of the XML settings file that CLAM outputs, rather than
#passing all parameters on the command line.


#If we run on Python 2.7, behave as much as Python 3 as possible
from __future__ import print_function, unicode_literals, division, absolute_import

#import some general python modules:
import sys
import os
import codecs
import re
import string

#import CLAM-specific modules. The CLAM API makes a lot of stuff easily accessible.
import clam.common.data
import clam.common.status

#When the wrapper is started, the current working directory corresponds to the project directory, input files are in input/ , output files should go in output/ .

#make a shortcut to the shellsafe() function
shellsafe = clam.common.data.shellsafe

#this script takes three arguments from CLAM: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY  (as configured at COMMAND= in the service configuration file)
datafile = sys.argv[1]
statusfile = sys.argv[2]
outputdir = sys.argv[3]

#If you make use of CUSTOM_FORMATS, you need to import your service configuration file here and set clam.common.data.CUSTOM_FORMATS
#Moreover, you can import any other settings from your service configuration file as well:

#from yourserviceconf import CUSTOM_FORMATS

#Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml)), always pass CUSTOM_FORMATS as second argument if you make use of it!
clamdata = clam.common.data.getclamdata(datafile)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

clam.common.status.write(statusfile, "Starting...")

#SOME EXAMPLES (uncomment and adapt what you need)

#-- Iterate over the program --

# The 'program' describes exactly what output files will be generated on the
# basis of what input files. It is the concretisation of the profiles and is the
# most elegant method to set up your wrapper.

#for outputfilename, outputtemplate in clamdata.program.getoutputpairs():
#   if you expect just a single input file for this output file, you can use this:
#   inputfilename, inputtemplate = next(clamdata.program.getinputpairs(outputfilename))
#   ...do your thing... e.g., invoke a process that generates outputfilename on the basis of inputfilename (see the invoke your actual system example below)

#   if, on the other hand, you expect multiple input files, then you can iterate over them:
#   for inputfilename, inputtemplate in clamdata.program.getinputpairs(outputfilename):
#       ...
#   ...do your thing... e.g., invoke a process that generates outputfilename on the basis all inputfilenames

#-- Iterate over all input files? --

#for inputfile in clamdata.input:
#   inputtemplate = inputfile.metadata.inputtemplate
#   inputfilepath = str(inputfile)
#   encoding = inputfile.metadata['encoding'] #Example showing how to obtain metadata parameters

#(Note: These iterations will fail if you change the current working directory, so make sure to set it back to the initial path if you do need to change it)

#-- Grab a specific input file? (by input template) --
#inputfile = clamdata.inputfile('replace-with-inputtemplate-id')
#inputfilepath = str(inputfile)

#-- Read global parameters? --
#parameter = clamdata['parameter_id']

#-- Invoke your actual system? --
# note the use of the shellsafe() function that wraps a variable in the
# specified quotes (second parameter) and makes sure the value doesn't break
# out of the quoted environment! Can be used without the quote too, but will be
# do much stricter checks then to ensure security.

#os.system("system.pl " + shellsafe(inputfilepath,'"') );

# Rather than execute a single system, call you may want to invoke it multiple
# times from within one of the iterations.

#A nice status message to indicate we're done
clam.common.status.write(statusfile, "Done",100) # status update

sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
