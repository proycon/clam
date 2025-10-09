#!/bin/sh

# Should run in a Python virtual environment ideally

TESTDIR=$(dirname "$0")
cd "$TESTDIR" || exit 1
HOSTNAME=$(hostname)


echo "Checking installation..." >&2

GOOD=1
FAILMSG=""

if ! command -v clamservice 2>/dev/null; then
   echo "ERROR: clamservice not found (run this script in a virtual environment with clam installed)" >&2
   FAILMSG="$FAILMSG clamservice"
   GOOD=0
fi

if ! command -v clamnewproject 2>/dev/null; then
   echo "ERROR: clamnewproject not found" >&2
   FAILMSG="$FAILMSG clamnewproject"
   GOOD=0
fi

cd /tmp || exit 2
if ! clamnewproject -f clamnewprojecttest --noninteractive; then
   echo "ERROR: clamnewproject didn't run well" >&2
   FAILMSG="$FAILMSG clamnewproject"
   GOOD=0
fi
rm -Rf clamnewprojecttest 2> /dev/null
cd -

if ! command -v clamdispatcher 2>/dev/null; then
   echo "ERROR: clamdispatcher not found" >&2
   FAILMSG="$FAILMSG clamdispatcher"
   GOOD=0
fi

if ! command -v clamclient 2>/dev/null; then
   echo "ERROR: clamclient not found" >&2
   FAILMSG="$FAILMSG clamclient"
   GOOD=0
fi

echo "  ..ok" >&2

echo "Running parameter tests:" >&2
if ! python parametertest.py; then
   echo "ERROR: Parameter test failed!!" >&2
   FAILMSG="$FAILMSG parametertest"
   GOOD=0
fi

echo "Running data tests:" >&2
if ! python datatest.py; then
   echo "ERROR: Data test failed!!" >&2
   FAILMSG="$FAILMSG datatest"
   GOOD=0
fi

echo "Stopping all running clam services" >&2
pkill -f clamservice
sleep 2

echo "Starting clam textstats service" >&2
clamservice -d clam.config.textstats 2> servicetest.server.log &
sleep 5

echo "Running service tests:" >&2
if ! python servicetest.py; then
   echo "ERROR: Service test failed!!" >&2
   GOOD=0
   FAILMSG="$FAILMSG servicetest"
   echo "<--------------------- servicetest.server.log --------------------------------->" >&2
   cat servicetest.server.log >&2
   echo "</-------------------- servicetest.server.log --------------------------------->" >&2
fi

echo "Stopping clam service" >&2
pkill -f clamservice


echo "Starting clam service 'authtest'" >&2
clamservice -d clam.config.authtest 2> authtest.server.log &
sleep 5


echo "Running authentication tests:" >&2
if ! python authtest.py; then
   echo "ERROR: Authentication test failed!!" >&2
   GOOD=0
   FAILMSG="$FAILMSG authtest"
   echo "<--------------------- authtest.server.log --------------------------------->" >&2
   cat authtest.server.log >&2
   echo "</-------------------- authtest.server.log --------------------------------->" >&2
fi

echo "Stopping clam service" >&2
pkill -f clamservice
sleep 2

echo "Starting clam service 'forwardauthtest'" >&2
clamservice -d clam.config.forwardauthtest 2> forwardauthtest.server.log &
sleep 5

#simple curl test:
if ! curl -f -H "X-Custom-User: test" "http://$HOSTNAME:8080/"; then
   echo "ERROR: Forwarded authentication failure (false negative)" >&2
   echo "<--------------------- forwardauthtest.server.log --------------------------------->" >&2
   cat forwardauthtest.server.log >&2
   echo "</-------------------- forwardauthtest.server.log --------------------------------->" >&2
   FAILMSG="$FAILMSG forwardauthtest"
   GOOD=0
fi

if curl -f "http://$HOSTNAME:8080/"; then
   echo "ERROR: Forwarded authentication failure (false positive)" >&2
   echo "<--------------------- forwardauthtest.server.log --------------------------------->" >&2
   cat forwardauthtest.server.log >&2
   echo "</-------------------- forwardauthtest.server.log --------------------------------->" >&2
   FAILMSG="$FAILMSG forwardauthtest"
   GOOD=0
fi

echo "Stopping clam service" >&2
pkill -f clamservice
sleep 2

echo "Starting clam service 'actiontest'" >&2
clamservice -d clam.config.actiontest 2> actiontest.server.log &
sleep 5

echo "Running actions tests:" >&2
if ! python actiontest.py; then
   echo "ERROR: Action test failed!!" >&2
   GOOD=0
   FAILMSG="$FAILMSG actiontest"
   echo "<--------------------- actiontest.server.log --------------------------------->" >&2
   cat actiontest.server.log >&2
   echo "</-------------------- actiontest.server.log --------------------------------->" >&2
fi

echo "Stopping clam service" >&2
pkill -f clamservice 2> /dev/null
sleep 2

echo "Starting clam service 'authactiontest'" >&2
clamservice -d clam.config.authactiontest 2> authactiontest.server.log &
sleep 5

echo "Running actions tests:" >&2
if ! python authactiontest.py; then
   echo "ERROR: AuthAction test failed!!" >&2
   GOOD=0
   FAILMSG="$FAILMSG authactiontest"
   echo "<--------------------- authactiontest.server.log --------------------------------->" >&2
   cat authactiontest.server.log >&2
   echo "</-------------------- authactiontest.server.log --------------------------------->" >&2
fi

echo "Stopping clam service" >&2
pkill -f clamservice 2> /dev/null
sleep 2

echo "Starting clam service 'constrainttest'" >&2
clamservice -d clam.config.constrainttest 2> constrainttest.server.log &
sleep 5

echo "Running constraint tests:" >&2
if ! python constrainttest.py; then
   echo "ERROR: constraint test failed!!" >&2
   FAILMSG="$FAILMSG constrainttest"
   GOOD=0
   echo "<--------------------- constrainttest.server.log --------------------------------->" >&2
   cat constrainttest.server.log >&2
   echo "</-------------------- constrainttest.server.log --------------------------------->" >&2
fi

echo "Stopping clam service" >&2
pkill -f clamservice 2> /dev/null
sleep 2

if [ $GOOD -eq 1 ]; then
    echo "Done, all tests passed!" >&2
    exit 0
else
    echo "TESTS FAILED!!!! $FAILMSG" >&2
    exit 1
fi




