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
import glob


#import CLAM-specific modules:
import clam.common.data
import clam.common.status
import clam.common.parameters
import clam.common.formats



#this script takes three arguments: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY
bindir = sys.argv[1]
inputdir = sys.argv[2]
datafile = sys.argv[3]
statusfile = sys.argv[4]
outputdir = sys.argv[5]



#Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml))
clamdata = clam.common.data.getclamdata(datafile)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

clam.common.status.write(statusfile, "Starting...")

#assemble parameters for Frog:

inputfiles = list(glob.glob(inputdir + '/*.xml'))
opts = ""
if 'lowercase' in clamdata and clamdata['lowercase']:
    opts += " --lower"
if 'n' in clamdata and clamdata['n']:
    opts += " --ngram " + str(clamdata['n'])

r = os.system("FoLiA-stats -t 1 -o " + outputdir + "/output " + opts + " " + " ".join(inputfiles))


clam.common.status.write(statusfile, "Done",100)

sys.exit(r) #non-zero exit codes indicate an error!
