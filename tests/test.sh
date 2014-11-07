#!/bin/bash

TESTDIR=`dirname $0`
cd $TESTDIR


echo "Checking installation..." >&2

GOOD=1

which clamservice 2>/dev/null
if [ $? -ne 0 ]; then
   echo "ERROR: clamservice not found" >&2
   GOOD=0
fi

which clamnewproject 2>/dev/null
if [ $? -ne 0 ]; then
   echo "ERROR: clamnewproject not found" >&2
   GOOD=0
fi

which clamdispatcher 2>/dev/null
if [ $? -ne 0 ]; then
   echo "ERROR: clamdispatcher not found" >&2
   GOOD=0
fi

which clamclient 2>/dev/null
if [ $? -ne 0 ]; then
   echo "ERROR: clamclient not found" >&2
   GOOD=0
fi

echo "  ..ok" >&2


echo "Running data tests:" >&2
python datatest.py 
if [ $? -ne 0 ]; then
   echo "ERROR: Data test failed!!" >&2
   GOOD=0
fi

echo "Stopping all running clam services" >&2
kill $(ps aux | grep 'clamservice' | awk '{print $2}') 2>/dev/null
sleep 2

echo "Starting clam textstats service" >&2
clamservice clam.config.textstats 2> servicetest.server.log &
sleep 2

echo "Running service tests:" >&2
python servicetest.py 
if [ $? -ne 0 ]; then
    echo "ERROR: Service test failed!!" >&2
   GOOD=0
   echo "<--------------------- servicetest.server.log --------------------------------->" >&2
   cat servicetest.server.log >&2
   echo "</-------------------- servicetest.server.log --------------------------------->" >&2
fi

echo "Stopping clam service" >&2
kill $(ps aux | grep 'clamservice' | awk '{print $2}') 2>/dev/null


echo "Starting clam service 'authtest'" >&2
clamservice clam.config.authtest 2> authtest.server.log &
sleep 3


echo "Running authentication tests:" >&2
python authtest.py 
if [ $? -ne 0 ]; then
   echo "ERROR: Authentication test failed!!" >&2
   GOOD=0
   echo "<--------------------- authtest.server.log --------------------------------->" >&2
   cat authtest.server.log >&2
   echo "</-------------------- authtest.server.log --------------------------------->" >&2
fi

echo "Stopping clam service" >&2
kill $(ps aux | grep 'clamservice' | awk '{print $2}') 2>/dev/null
sleep 2 

if [ $GOOD -eq 1 ]; then
    echo "Done, all tests passed!" >&2
    exit 0
else
    echo "TESTS FAILED!!!!" >&2
    exit 1
fi




