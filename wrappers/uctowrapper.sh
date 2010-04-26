#!/bin/bash
# Wrapper for UCTO, called by CLAM ('blackbox')
# assumes ucto is installed on the system

STATUSFILE=$1
INPUTDIR=$2
OUTPUTDIR=$3
PARAMETERS=${@:4}



for f in $INPUTDIR*.txt; do
    filename=`basename $f`
    echo "Processing $filename" > $STATUSFILE
    #note that here the $PARAMETERS are passed just as they were received by CLAM
    ucto $PARAMETERS < $f > ${OUTPUTDIR}$filename.tok 
done

