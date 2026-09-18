#!/bin/sh

#param $1 is the flag -t

echo "$2" | socat -t 2 - tcp:localhost:7777
