#!/usr/bin/env python
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

#import some general python modules:
import sys
import os
import codecs
import re

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




    for i, inputfile in enumerate(clamdata.input):
        #Update our status message to let CLAM know what we're doing
        p = round((i/float(len(clamdata.input)))*100)


        filename = os.path.basename(str(inputfile))
        #strip extension
        filename = filename[:-4]

        inputtemplate = inputfile.metadata.inputtemplate

        os.chdir(outputdir)

        if inputtemplate == 'textinput_tok':
            os.symlink(str(inputfile),outputdir + '/' + filename + '.txt')
        elif inputtemplate == 'textinput_untok':
            #we'll need to tokenise first
            language = inputfile.metadata['language']
            clam.common.status.write(statusfile, "Tokenising " + filename + "...", p)
            uctooptions = ''
            if inputfile.metadata['sentenceperline_input']:
                uctooptions += "-m "
            if inputfile.metadata['sentenceperline_output']:
                uctooptions += "-n "
            os.system(bindir + 'ucto -L ' + shellsafe(language,"'")+ ' ' + uctooptions + ' ' + shellsafe(str(inputfile),'"') + ' > ' + shellsafe(outputdir +'/'+ filename + '.txt',"'"))

        elif inputtemplate == 'foliainput':
            os.symlink(str(inputfile),outputdir + '/' + filename + '.xml')

        clam.common.status.write(statusfile, "Class Encoding " + filename + "...", p)
        if inputtemplate == 'foliainput':
            os.system(bindir + 'colibri-classencode ' + outputdir+'/'+filename +'.xml')
        else:
            os.system(bindir + 'colibri-classencode ' + outputdir+'/'+filename +'.txt')

        doindex = clamdata['indexing'] or clamdata['cooc'] or clamdata['npmi']

        options = ""
        if not doindex:
            options += "-u "
        if clamdata['skipgrams']:
            options += "-s "
        options += "-t " + str(clamdata['mintokens']) + " "
        options += "-m " + str(clamdata['minlength']) + " "
        options += "-l " + str(clamdata['maxlength']) + " "

        clam.common.status.write(statusfile, "Building pattern model for " + filename + "...", p)
        r = os.system(bindir + 'colibri-patternmodeller ' + options + ' -f ' + shellsafe(filename + '.colibri.dat',"'") + " -c " + shellsafe(filename + ".colbiri.cls","'") + " -o " + shellsafe(filename + ".colibri.patternmodel","'") )
        if r != 0:
            clam.common.status.write(statusfile, "Failure in building patternmodel for " + filename,100) # status update
            sys.exit(1)



        cmd = bindir + 'colibri-patternmodeller ' + options + ' -i ' + shellsafe(filename + '.colibri.patternmodel',"'") + " -c " + shellsafe(filename + ".colbiri.cls","'")

        if clamdata['extract']:
            clam.common.status.write(statusfile, "Outputting pattern list for " + filename + "...", p)
            r = os.system(cmd + " -P > " + filename + ".patterns.csv")
        elif clamdata['report']:
            clam.common.status.write(statusfile, "Computing and outputting report for " + filename + "...", p)
            r = os.system(cmd + " -R > " + filename + ".report.txt")
        elif clamdata['histogram']:
            clam.common.status.write(statusfile, "Computing and outputting histogram for " + filename + "...", p)
            r = os.system(cmd + " -H > " + filename + ".histogram.csv")
        elif clamdata['reverseindex']:
            clam.common.status.write(statusfile, "Computing and outputting reverse index for " + filename + "...", p)
            r = os.system(cmd + " -r " + filename + ".colibri.dat" + " -Z > " + filename + ".reverseindex.csv")
        elif clamdata['cooc'] > 0:
            clam.common.status.write(statusfile, "Computing and outputting co-occurrences for " + filename + "...", p)
            r = os.system(cmd + " -r " + filename + ".colibri.dat" + " -C " + str(clamdata['cooc']) + " > " + filename + ".cooc.csv")
        elif clamdata['npmi'] > -1:
            clam.common.status.write(statusfile, "Computing and outputting co-occurrences (npmi) for " + filename + "...", p)
            r = os.system(cmd + " -r " + filename + ".colibri.dat" + " -Y " + str(clamdata['npmi']) + " > " + filename + ".npmi.csv")

        if r != 0:
            clam.common.status.write(statusfile, "Error processing " + filename,100) # status update
            sys.exit(1)


    #A nice status message to indicate we're done
    clam.common.status.write(statusfile, "Done",100) # status update

    sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
