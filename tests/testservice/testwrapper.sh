#!/bin/sh

if [ "$1" = "-t" ]; then
    echo "starting (action)...">&2
    #string passed (CLAM action)
    echo "$2" | tr "[:lower:]" "[:upper:]"
    ret=$?
else
    echo "starting (project)...">&2
    #file passed (CLAM project)
    tr "[:lower:]" "[:upper:]" < "$1" > "$(basename "$1")"
    ret=$?
fi

#artificial sleep to simulate longer running processes and allow more tests
sleep 5

if [ $ret = 0 ]; then
    echo "done...">&2
else
    echo "failed...">&2
fi
exit $ret
