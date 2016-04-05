#!/usr/bin/env bash

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

#This is the shell version of the system wrapper script. You can also use the
#Python version, which is generally more powerful as it parses the XML settings 
#file for you, unlike this template. Using Python is recommended for more
#complex webservices and for additional security.

#this script takes three arguments from CLAM: $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY. (as configured at COMMAND= in the service configuration file)
STATUSFILE=$1
INPUTDIRECTORY=$2
OUTPUTDIRECTORY=$3

#If $PARAMETERS was passed COMMAND= in the service configuration file, the remainder of the arguments are custom parameters for which you either need to do your own parsing, or you pass them directly to your application
PARAMETERS=${@:4}

#Output a status message to the status file that users will see in the interface
echo "Starting..." >> $STATUSFILE

#Example parameter parsing using getopt:
#while getopts ":h" opt "$PARAMETERS"; do
#  case $opt in
#    h)
#      echo "Help option was triggered" >&2
#      ;;
#    \?)
#      echo "Invalid option: -$OPTARG" >&2
#      ;;
#  esac
#done

#Loop over all input files, here we assume they are txt files, adapt to your situation:
for inputfile in $INPUTDIRECTORY/*.txt; do
    #get name of output file on the basis of input file
    filename=`basename $inputfile`
    outputfile="$OUTPUTDIRECTORY/$filename"
    #Invoke your actual system, whatever it may be, adapt accordingly
    yoursystem $PARAMETERS < $inputfile > $outputfile
done

echo "Done." >> $STATUSFILE



