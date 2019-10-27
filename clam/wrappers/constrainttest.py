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

#This is a test wrapper, meant to illustrate how easy it is to set
#up a wrapper script for your system using Python and the CLAM Client API.
#We make use of the XML configuration file that CLAM outputs, rather than
#passing all parameters on the command line.

#This script will be called by CLAM and will run with the current working directory set to the specified project directory


#import some general python modules:
import sys
import os
import io
import string
from collections import defaultdict

#import CLAM-specific modules. The CLAM API makes a lot of stuff easily accessible.
import clam.common.data
import clam.common.status

import folia.main as folia



##########################################################################################################
#   Auxiliary functions (not using CLAM API at all, SKIP THIS if you're only interested in the wrapper script! )
#########################################################################################################





def dicttotext(d, sort=False, max = 0):
    """Function for converting dictionary to plaintext output, optionally with some (reverse) sorting"""
    if sort:
        f = lambda x: sorted(x, key=lambda y: -1 * y[1])
    else:
        f = lambda x: x

    output = ""
    for i, (key, value) in enumerate(f(d.items())):
        output += key + "\t" + str(value) + "\n"
        if max != 0 and i >= max:
            break
    return output


#########################################################################################################
#       MAIN WRAPPER
#########################################################################################################


if __name__ == "__main__":

    #this script takes three arguments from CLAM: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY  (as configured at COMMAND= in the service configuration file)
    datafile = sys.argv[1]
    statusfile = sys.argv[2]
    outputdir = sys.argv[3]

    #Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml))
    clamdata = clam.common.data.getclamdata(datafile)

    #You now have access to all data. A few properties at your disposition now are:
    # clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

    clam.common.status.write(statusfile, "Starting...")

    count = defaultdict(int)
    for i, inputfile in enumerate(clamdata.input):
        #Update our status message to let CLAM know what we're doing
        clam.common.status.write(statusfile, "Processing " + os.path.basename(str(inputfile)) + "...", round((i/float(len(clamdata.input)))*100))

        doc = folia.Document(file=str(inputfile))
        for pos in doc.select(folia.PosAnnotation):
            count[pos.cls] += 1

    #Write overall statistics output for this file
    f = io.open(outputdir + 'posfreqlist.tsv','w',encoding='utf-8')
    f.write(dicttotext(count))
    f.close()


    #A nice status message to indicate we're done
    clam.common.status.write(statusfile, "Done",100) # status update

    sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
