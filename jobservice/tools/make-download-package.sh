#!/bin/bash
PROJECT=$1
FORMAT=$2
if (( $FORMAT == "zip" )); then
    zip -r $PROJECT.zip output 
    mv -f $PROJECT.zip output/
fi
if (( $FORMAT == "tar.gz" )); then
    tar -czf $PROJECT.tar.gz output 
    mv -f $PROJECT.tar.gz output/
fi
if (( $FORMAT == "tar.bz2" )); then
    tar -cjf $PROJECT.tar.bz2 output 
    mv -f $PROJECT.tar.bz2 output/
fi



