#!/bin/bash
# Wrapper for UCTO, called by CLAM ('blackbox')
# assumes ucto is installed on the system

INPUTDIR=$1
OUTPUTDIR=$2
PARAMETERS=${@:$3}

for f in $INPUTDIR*.txt; do
    filename=basename $f
    ucto $PARAMETERS < $f > ${OUTPUTDIR}$filename.tok
done

