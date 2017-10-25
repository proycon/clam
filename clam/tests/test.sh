#!/bin/bash

# Should run in a Python virtual environment ideally

TESTDIR=`dirname $0`
cd $TESTDIR
HOSTNAME=$(hostname)


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

cd /tmp
clamnewproject -f clamnewprojecttest
if [ $? -ne 0 ]; then
   echo "ERROR: clamnewproject didn't run well" >&2
   GOOD=0
fi
rm -Rf clamnewprojecttest 2> /dev/null
cd -

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

echo "Running parameter tests:" >&2
python parametertest.py
if [ $? -ne 0 ]; then
   echo "ERROR: Parameter test failed!!" >&2
   GOOD=0
fi

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
clamservice -d clam.config.textstats 2> servicetest.server.log &
sleep 5

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
clamservice -d clam.config.authtest 2> authtest.server.log &
sleep 5


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

echo "Starting clam service 'forwardauthtest'" >&2
clamservice -d clam.config.forwardauthtest 2> forwardauthtest.server.log &
sleep 5

#simple curl test:
curl -f -H "REMOTE_USER: test" http://$HOSTNAME:8080/
if [ $? -ne 0 ]; then
   echo "ERROR: Forwarded authentication failure" >&2
   GOOD=0
fi


echo "Stopping clam service" >&2
kill $(ps aux | grep 'clamservice' | awk '{print $2}') 2>/dev/null
sleep 2

echo "Starting clam service 'actiontest'" >&2
clamservice -d clam.config.actiontest 2> actiontest.server.log &
sleep 5

echo "Running actions tests:" >&2
python actiontest.py
if [ $? -ne 0 ]; then
   echo "ERROR: Action test failed!!" >&2
   GOOD=0
   echo "<--------------------- actiontest.server.log --------------------------------->" >&2
   cat actiontest.server.log >&2
   echo "</-------------------- actiontest.server.log --------------------------------->" >&2
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




