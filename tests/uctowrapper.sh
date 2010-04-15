#!/bin/bash
# Wrapper for UCTO, called by CLAM ('blackbox')
# assumes ucto is installed on the system

STATUSFILE=$1
INPUTDIR=$2
OUTPUTDIR=$3
PARAMETERS=${@:4}

echo "Abruptly waking up from pleasant dreams..." > $STATUSFILE
sleep 10
echo "Making oatmeal for breakfast" > $STATUSFILE
sleep 10
echo "Brushing teeth... Nobody likes smelly webservices " > $STATUSFILE
sleep 10
echo "Yeah yeah, don't push me, going to work already!" > $STATUSFILE
sleep 10

for f in $INPUTDIR*.txt; do
    filename=`basename $f`
    echo "UCTOWRAPPER: ucto $PARAMETERS < $f > ${OUTPUTDIR}$filename.tok"
    echo "Processing $filename" > $STATUSFILE
    ucto $PARAMETERS < $f > ${OUTPUTDIR}$filename.tok
    sleep 5
done

echo "Yay! Done working" > $STATUSFILE
sleep 10
echo "Rushing home" > $STATUSFILE
sleep 10
echo "Cooking dinner, eating and elaborately bathing" > $STATUSFILE
sleep 10
echo "All done, back to bed!" > $STATUSFILE
sleep 10

