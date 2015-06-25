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

from __future__ import print_function, unicode_literals, division, absolute_import

#import some general python modules:
import sys
import os
import io
import string

#import CLAM-specific modules. The CLAM API makes a lot of stuff easily accessible.
import clam.common.data
import clam.common.status



##########################################################################################################
#   Auxiliary functions (not using CLAM API at all, SKIP THIS if you're only interested in the wrapper script! )
#########################################################################################################



def crude_tokenizer(line):
    """This is a very crude tokenizer from pynlpl"""
    tokens = []
    buffer = ''
    for c in line.strip():
        if c == ' ' or c in string.punctuation:
            if buffer:
                tokens.append(buffer)
                buffer = ''
        else:
            buffer += c
    if buffer: tokens.append(buffer)
    return tokens


def calcstats(filename, encoding, casesensitive=True):
    #This is the actual core program, a very simple statistics gatherer. This function is totally independent of the CLAM API.

    global overallstats, overallfreqlist

    freqlist = {}
    f = io.open(filename,'r', encoding=encoding)
    lines = types = tokens = characters = 0
    for line in f:
        lines += 1
        if casesensitive:
            words = crude_tokenizer(line)
        else:
            words = crude_tokenizer(line)
        if casesensitive:
            types += len(set(words))
        else:
            types += len(set([ x.lower() for x in words]))
        tokens += len(words)
        for word in words:
            if not casesensitive:
                word = word.lower()
            if not word in freqlist:
                freqlist[word] = 1
            else:
                freqlist[word] += 1
        characters += len(line)
    f.close()

    stats = {'lines': lines, 'types': types,'tokens': tokens, 'characters': characters}

    for key, value in stats.items():
        if key in overallstats:
            overallstats[key] += value
        else:
            overallstats[key] = value

    for key, value in freqlist.items():
        if key in overallfreqlist:
            overallfreqlist[key] += value
        else:
            overallfreqlist[key] = value


    return stats, freqlist


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

    #Specific datatypes for this particular application (global variables)
    overallstats = {}  #will hold overall statistics
    overallfreqlist = {} #will hold overall frequency list

    #Read a user-defined parameter
    try:
        freqlistlimit = clamdata['freqlistlimit']
    except KeyError:
        freqlistlimit = 0


    for i, inputfile in enumerate(clamdata.input):
        #Update our status message to let CLAM know what we're doing
        clam.common.status.write(statusfile, "Processing " + os.path.basename(str(inputfile)) + "...", round((i/float(len(clamdata.input)))*100))

        #We need one of the metadata fields
        encoding = inputfile.metadata['encoding']

        #Calling a function containing the actual core of this program (totally CLAM unaware).
        #In other scenarios, this could be where you invoke other scripts/programs through os.system()
        localstats, localfreqlist =  calcstats(str(inputfile), encoding, clamdata['casesensitive'])

        #Write statistics output for this file
        #Note 1) The filenames must always correspond to what has been defined in PROFILES in the service configuration file!
        #Note 2) The output metadata will be generated by CLAM itself, so there's no need to do that here.
        f = io.open(outputdir + os.path.basename(str(inputfile)) + '.stats','w',encoding=encoding)
        f.write(dicttotext(localstats))
        f.close()

        #Write frequency list output for this file
        f = io.open(outputdir + os.path.basename(str(inputfile)) + '.freqlist','w',encoding=encoding)
        f.write(dicttotext(localfreqlist, True, freqlistlimit))
        f.close()


    clam.common.status.write(statusfile, "Writing overall statistics...",99)  #status update

    #Write overall statistics output for this file
    f = io.open(outputdir + 'overall.stats','w',encoding='utf-8')
    f.write(dicttotext(overallstats))
    f.close()

    #Write overall frequency list output for this file
    f = io.open(outputdir + 'overall.freqlist','w',encoding='utf-8')
    f.write(dicttotext(overallfreqlist, True, freqlistlimit ))
    f.close()

    if clamdata['createlexicon']:
        #Write overall frequency list output for this file
        f = io.open(outputdir + 'overall.lexicon','w',encoding='utf-8')
        for word in sorted(overallfreqlist.keys()):
            f.write(word+"\n")
        f.close()

    #A nice status message to indicate we're done
    clam.common.status.write(statusfile, "Done",100) # status update

    sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
