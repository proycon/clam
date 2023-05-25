#!/usr/bin/env sh

###############################################################
# -- CLAM Wrapper script Template --
###############################################################

#This is a template wrapper which you can use a basis for writing your own
#system wrapper script. The system wrapper script is called by CLAM, its job it
#to call your actual tool.

#you can use this function as-is to handle errors
die() {
    echo "ERROR: $*">&2
    echo "Failed: $*">> "$STATUSFILE"
    exit 1
}

#This script will be called by CLAM and will run with the current working directory set to the specified project directory

#This is the shell version of the system wrapper script. You can also use the
#Python version, which is generally more powerful as it parses the XML settings 
#file for you, unlike this template. Using Python is recommended for more
#complex webservices and for additional security.

#this script takes three arguments from CLAM: $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY. (as configured at COMMAND= in the service configuration file)
STATUSFILE=$1
shift
INPUTDIRECTORY=$2
shift
OUTPUTDIRECTORY=$3
shift

# If $PARAMETERS was passed via COMMAND= in the service configuration file;
# the remainder of the arguments in $@ are now custom parameters for which you either need to do your own parsing, or you pass them directly to your application

#Output a status message to the status file that users will see in the interface
echo "Starting..." >> "$STATUSFILE"

#Example parameter parsing using getopt:

#while getopts ":h" opt "$@"; do
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
for inputfile in "$INPUTDIRECTORY/"*.txt; do
    #get name of output file on the basis of input file
    filename=$(basename "$inputfile")
    outputfile="$OUTPUTDIRECTORY/$filename"

    #Invoke your actual system, whatever it may be, adapt accordingly!
    # If $PARAMETERS was passed via COMMAND= in the service configuration file;
    # the remainder of the arguments in $@ are now custom parameters for which you either need to do your own parsing, or you pass them directly to your application
    yoursystem "$@" < "$inputfile" > "$outputfile" || die "System failed when processing $filename"
done

echo "Done." >> "$STATUSFILE"
