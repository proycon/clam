#!/usr/bin/env python3
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
#       by Maarten van Gompel (proycon)
#       http://proycon.github.io/clam/
#       Centre for Language and Speech Technology  / Language Machines
#       Radboud University Nijmegen
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


#curdir = os.getcwd()

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


        if inputtemplate == 'textinput_tok':
            os.symlink(os.path.abspath(str(inputfile)),outputdir + '/' + filename + '.txt')
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
            os.symlink(os.path.abspath(str(inputfile)),outputdir + '/' + filename + '.xml')



        clam.common.status.write(statusfile, "Class Encoding " + filename + "...", p)
        if inputtemplate == 'foliainput':
            os.system(bindir + 'colibri-classencode ' +  outputdir+'/'+filename +'.xml')
        else:
            os.system(bindir + 'colibri-classencode ' + outputdir+'/'+filename +'.txt')

        #files will be in the wrong place after classencode, move:
        os.rename(filename+'.colibri.cls', outputdir+'/'+filename+'.colibri.cls')
        os.rename(filename+'.colibri.dat', outputdir+'/'+filename+'.colibri.dat')

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
        r = os.system(bindir + 'colibri-patternmodeller ' + options + ' -f ' + shellsafe(outputdir + '/' + filename + '.colibri.dat',"'") + " -c " + shellsafe(outputdir + '/' + filename + ".colibri.cls","'") + " -o " + shellsafe(outputdir + '/' + filename + ".colibri.patternmodel","'") )
        if r != 0:
            clam.common.status.write(statusfile, "Failure in building patternmodel for " + filename,100) # status update
            sys.exit(1)



        cmd = bindir + 'colibri-patternmodeller ' + options + ' -i ' + shellsafe(outputdir + '/' + filename + '.colibri.patternmodel',"'") + " -c " + shellsafe(outputdir + '/' + filename + ".colibri.cls","'")

        if clamdata['extract']:
            clam.common.status.write(statusfile, "Outputting pattern list for " + filename + "...", p)
            r = os.system(cmd + " -P > " + outputdir + '/' + filename + ".patterns.csv")
        if clamdata['report']:
            clam.common.status.write(statusfile, "Computing and outputting report for " +  filename + "...", p)
            r = os.system(cmd + " -R > " + outputdir + '/' + filename + ".report.txt")
        if clamdata['histogram']:
            clam.common.status.write(statusfile, "Computing and outputting histogram for " + filename + "...", p)
            r = os.system(cmd + " -H > " + outputdir + '/' + filename + ".histogram.csv")
        if clamdata['reverseindex']:
            clam.common.status.write(statusfile, "Computing and outputting reverse index for " + filename + "...", p)
            r = os.system(cmd + " -r " + outputdir + '/' + filename + ".colibri.dat" + " -Z > " + filename + ".reverseindex.csv")
        if clamdata['cooc'] > 0:
            clam.common.status.write(statusfile, "Computing and outputting co-occurrences for " + filename + "...", p)
            r = os.system(cmd + " -r " + outputdir + '/' + filename + ".colibri.dat" + " -C " + str(clamdata['cooc']) + " > " + outputdir + '/' + filename + ".cooc.csv")
        print("NPMI=",clamdata['npmi'], type(clamdata['npmi']),file=sys.stderr)
        if clamdata['npmi'] > -1:
            clam.common.status.write(statusfile, "Computing and outputting co-occurrences (npmi) for " + filename + "...", p)
            r = os.system(cmd + " -r " + outputdir + '/' + filename + ".colibri.dat" + " -Y " + str(clamdata['npmi']) + " > " + outputdir + '/' + filename + ".npmi.csv")

        if r != 0:
            clam.common.status.write(statusfile, "Error processing " + filename,100) # status update
            sys.exit(1)


    #A nice status message to indicate we're done
    clam.common.status.write(statusfile, "Done",100) # status update

    sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
