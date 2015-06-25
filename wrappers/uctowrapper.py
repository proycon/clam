#!/usr/bin/env python3
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Wrapper script for Text Statistics --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       Licensed under GPLv3
#
###############################################################


from __future__ import print_function, unicode_literals, division, absolute_import

#import some general python modules:
import sys
import os

#import CLAM-specific modules. The CLAM API makes a lot of stuff easily accessible.
import clam.common.data
import clam.common.status

shellsafe = clam.common.data.shellsafe

if __name__ == "__main__":

    #this script takes three arguments from CLAM: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY  (as configured at COMMAND= in the service configuration file)
    bindir = sys.argv[1]
    datafile = sys.argv[2]
    statusfile = sys.argv[3]
    outputdir = sys.argv[4]

    #Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml))
    clamdata = clam.common.data.getclamdata(datafile)

    #You now have access to all data. A few properties at your disposition now are:
    # clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

    clam.common.status.write(statusfile, "Starting...")


    commandlineargs = clamdata.commandlineargs() #shell-safe by definition


    for i, inputfile in enumerate(clamdata.input):
        #Update our status message to let CLAM know what we're doing
        clam.common.status.write(statusfile, "Processing " + os.path.basename(str(inputfile)) + "...", round((i/float(len(clamdata.input)))*100))

        #We need one of the metadata fields
        language = inputfile.metadata['language']


        if clamdata['xml']:
            docid = None
            if 'documentid' in inputfile.metadata and inputfile.metadata['documentid']:
                docid = inputfile.metadata['documentid']
            if not docid:
                docid = "untitled"
            os.system(bindir + 'ucto -L ' + shellsafe(language,"'") + ' -x ' + shellsafe(docid,"'") + ' ' + commandlineargs + ' ' + shellsafe(str(inputfile),'"') + ' > ' + shellsafe(outputdir +'/'+ inputfile.filename.replace('.txt','') + '.xml','"'))
        elif clamdata['verbose']:
            os.system(bindir + 'ucto -L ' + shellsafe(language,"'")+ ' ' + commandlineargs + ' ' + shellsafe(str(inputfile),'"') + ' > ' + shellsafe(outputdir +'/'+ inputfile.filename.replace('.txt','') + '.vtok',"'"))
        else:
            os.system(bindir + 'ucto -L ' + shellsafe(language,"'")+ ' ' + commandlineargs + ' ' + shellsafe(str(inputfile),'"') + ' > ' + shellsafe(outputdir +'/'+ inputfile.filename.replace('.txt','') + '.tok',"'"))

    #A nice status message to indicate we're done
    clam.common.status.write(statusfile, "Done",100) # status update

    sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
