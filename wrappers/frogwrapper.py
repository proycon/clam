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


#This script will be called by CLAM and will run with the current working directory set to the specified project directory

from __future__ import print_function, unicode_literals, division, absolute_import

#general python modules:
import sys
import os


#import CLAM-specific modules:
import clam.common.data
import clam.common.status
import clam.common.parameters
import clam.common.formats

shellsafe = clam.common.data.shellsafe

#this script takes three arguments: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY
bindir = sys.argv[1]
datafile = sys.argv[2]
statusfile = sys.argv[3]
outputdir = sys.argv[4]


#os.environ['PYTHONPATH'] = bindir + '/../lib/python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor) + '/site-packages/frog' #Necessary for University of Tilburg servers (change or remove this in your own setup)

#Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml))
clamdata = clam.common.data.getclamdata(datafile)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

clam.common.status.write(statusfile, "Starting...")

#assemble parameters for Frog:


for i, inputfile in enumerate(clamdata.inputfiles('maininput')):
    cmdoptions = " --max-parser-tokens=200"

    if 'skip' in clamdata and clamdata['skip']:
        print("Skip options: ", "".join(clamdata['skip']),file=sys.stderr)
        cmdoptions += ' --skip=' + "".join(clamdata['skip'])


    clam.common.status.write(statusfile, "Processing " + os.path.basename(str(inputfile)) + "...")

    print("Processing " + os.path.basename(str(inputfile)) + "...", file=sys.stderr)
    outputstem = os.path.basename(str(inputfile))
    if outputstem[-4:] == '.xml' or outputstem[-4:] == '.txt': outputstem = outputstem[:-4]
    if 'sentenceperline' in inputfile.metadata and inputfile.metadata['sentenceperline']:
        cmdoptions += ' -n'
    if 'docid' in inputfile.metadata and inputfile.metadata['docid']:
        docid = inputfile.metadata['docid']
        print("\tDocID from metadata: " + docid,file=sys.stderr)
    else:
        docid = outputstem
        print("\tDocID from filename: " + docid, file=sys.stderr)
    docid = docid.replace(' ','-')
    docid = docid.replace("'",'')
    docid = docid.replace('"','')
    if not docid:
        docid = 'untitled'

    print("Invoking Frog",file=sys.stderr)
    r = os.system(bindir + "frog -c " + bindir + "../etc/frog/frog.cfg " + shellsafe(cmdoptions) + " -t " + shellsafe(str(inputfile),'"') + " --id=" + shellsafe(docid,"'") + " -X " + shellsafe(outputdir + outputstem + ".xml","'") + " -o " + shellsafe(outputdir + outputstem + ".frog.out","'") + " --threads=1")
    if r != 0:
        clam.common.status.write(statusfile, "Frog returned with an error whilst processing " + os.path.basename(str(inputfile) + " (plain text). Aborting"),100)
        sys.exit(1)

for i, inputfile in enumerate(clamdata.inputfiles('foliainput')):
    cmdoptions = " --max-parser-tokens=200"

    if 'skip' in clamdata and clamdata['skip']:
        cmdoptions += ' --skip=' + "".join(clamdata['skip'])


    clam.common.status.write(statusfile, "Processing " + os.path.basename(str(inputfile)))
    outputstem = os.path.basename(str(inputfile))
    if outputstem[-4:] == '.xml' or outputstem[-4:] == '.txt': outputstem = outputstem[:-4]

    print("Invoking Frog",file=sys.stderr)
    r = os.system(bindir + "frog -c " + bindir + "../etc/frog/frog.cfg " + shellsafe(cmdoptions) + " -x " + shellsafe(str(inputfile),'"') + " -X " + shellsafe(outputdir + outputstem + ".xml","'") + " -o " + shellsafe(outputdir + outputstem + ".frog.out","'") + " --threads=1")
    if r != 0:
        clam.common.status.write(statusfile, "Frog returned with an error whilst processing " + os.path.basename(str(inputfile) + " (FoLiA). Aborting"),100)
        sys.exit(1)

clam.common.status.write(statusfile, "Done",100)

sys.exit(0) #non-zero exit codes indicate an error!
