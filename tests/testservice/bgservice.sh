#!/bin/sh

# background service: a simple echo service

setsid socat TCP-LISTEN:7777,reuseaddr,fork EXEC:'cat',nofork &
pid=$!

#catch and propagate SIGTERM, important because background services must always be stoppable on request!
trap 'kill -TERM -- "-$pid" 2>/dev/null; wait "$pid"; exit 143' TERM INT

#wait
wait "$pid"
