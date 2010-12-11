#!/bin/bash

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- System wrapper for Frog--
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

# Note: this script is not very efficient yet, as it restarts Frog for each input file!

STATUSFILE=$1
INPUTDIR=$2
OUTPUTDIR=$3
PARAMETERS=${@:4}

TIMESTAMP=`date +%s`
echo -e "0%\t$TIMETAMP\tStarting" >> $STATUSFILE

INPUTCOUNT=`ls $INPUTDIR*.txt | wc -l`
COUNT=0
for f in $INPUTDIR*.txt; do
    let COUNT++
    COMPLETION=`echo "scale=6;x=($COUNT/$INPUTCOUNT)*100;scale=0;x/=1;x" | bc`
    filename=`basename $f`
    TIMESTAMP=`date +%s`
    echo -e "$COMPLETION%\t$TIMESTAMP\tRunning Frog on $filename" >> $STATUSFILE
    #echo "Running Tadpole $PARAMETERS -t $f > ${OUTPUTDIR}$filename.tadpole"
    #note that here the $PARAMETERS are passed just as they were received by CLAM
    Frog $PARAMETERS -t $f > ${OUTPUTDIR}$filename.frogged 
done

echo -e "100%\t$TIMETAMP\tDone with all files" >> $STATUSFILE

