#!/usr/bin/env python
#-*- coding:utf-8 -*-


###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Dispatcher --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/clam
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       Licensed under GPLv3
#
###############################################################


import sys
import os
import datetime
import subprocess
import time

VERSION = '0.9.7'

sys.path.append(sys.path[0] + '/..')
#os.environ['PYTHONPATH'] = sys.path[0] + '/..'


def mem(pid, size="rss"):
    """memory sizes: rss, rsz, vsz."""
    return int(os.popen('ps -p %d -o %s | tail -1' % (pid, size)).read())

def total_seconds(delta):
    return delta.days * 86400 + delta.seconds + (delta.microseconds / 1000000.0)

def main():
    if len(sys.argv) < 4:
        print >>sys.stderr,"[CLAM Dispatcher] ERROR: Invalid syntax, use clamdispatcher.py [pythonpath] settingsmodule projectdir cmd arg1 arg2 ... got: " + " ".join(sys.argv[1:])
        f = open('.done','w')
        f.write(str(1))
        f.close()
        if os.path.exists('.pid'): os.unlink('.pid')
        return 1

    offset = 0
    if '/' in sys.argv[1]:
        #os.environ['PYTHONPATH'] = sys.argv[1]
        for path in sys.argv[1].split(':'):
            print >>sys.stderr,"[CLAM Dispatcher] Adding to PYTHONPATH: " + path
            sys.path.append(path)
        offset = 1

    settingsmodule = sys.argv[1+offset]
    projectdir = sys.argv[2+offset]
    if projectdir[-1] != '/':
        projectdir += '/'

    cmd = " ".join(sys.argv[3+offset:])

    print >>sys.stderr, "[CLAM Dispatcher] Started (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ")"

    if not cmd:
        print >>sys.stderr, "[CLAM Dispatcher] FATAL ERROR: No command specified!"
        f = open(projectdir + '.done','w')
        f.write(str(1))
        f.close()
        if os.path.exists(projectdir + '.pid'): os.unlink(projectdir + '.pid')
        return 1
    elif not os.path.isdir(projectdir):
        print >>sys.stderr, "[CLAM Dispatcher] FATAL ERROR: Project directory "+ projectdir + " does not exist"
        f = open(projectdir + '.done','w')
        f.write(str(1))
        f.close()
        if os.path.exists(projectdir + '.pid'): os.unlink(projectdir + '.pid')
        return 1

    try:
        exec "import " + settingsmodule + " as settings"
    except ImportError as e:
        print >>sys.stderr, "[CLAM Dispatcher] FATAL ERROR: Unable to import settings module, settingsmodule is " + settingsmodule + ", error: " + str(e)
        f = open(projectdir + '.done','w')
        f.write(str(1))
        f.close()
        return 1

    settingkeys = dir(settings)
    if not 'DISPATCHER_POLLINTERVAL' in settingkeys:
        settings.DISPATCHER_POLLINTERVAL = 30
    if not 'DISPATCHER_MAXRESMEM' in settingkeys:
        settings.DISPATCHER_MAXRESMEM = 0
    if not 'DISPATCHER_MAXTIME' in settingkeys:
        settings.DISPATCHER_MAXTIME = 0

    print >>sys.stderr, "[CLAM Dispatcher] Running " + cmd

    process = subprocess.Popen(cmd,cwd=projectdir, shell=True, stderr=sys.stderr)
    begintime = datetime.datetime.now()
    if process:
        pid = process.pid
        print >>sys.stderr, "[CLAM Dispatcher] Running with pid " + str(pid) + " (" + begintime.strftime('%Y-%m-%d %H:%M:%S') + ")"
        sys.stderr.flush()
        f = open(projectdir + '.pid','w')
        f.write(str(pid))
        f.close()
    else:
        print >>sys.stderr, "[CLAM Dispatcher] Unable to launch process"
        sys.stderr.flush()
        f = open(projectdir + '.done','w')
        f.write(str(1))
        f.close()
        return 1

    #intervalf = lambda s: min(s/10.0, 15)
    abortchecktime = 0
    abort = False
    idle = 0
    done = False
    lastpolltime = datetime.datetime.now()


    while not done:
        d = total_seconds(datetime.datetime.now() - begintime)
        try:
            returnedpid, statuscode = os.waitpid(pid, os.WNOHANG)
            if returnedpid != 0:
                print >>sys.stderr, "[CLAM Dispatcher] Process ended (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ", " + str(d)+"s) "
                done = True
        except OSError: #no such process
            print >>sys.stderr, "[CLAM Dispatcher] Process lost! (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ", " + str(d)+"s)"
            statuscode = 1
            done = True

        if done:
            break

        abortchecktime += d
        if abortchecktime >= d+0.1 or abortchecktime >= 10: #every 10 seconds, faster at beginning
            abortchecktime = 0
            if os.path.exists(projectdir + '.abort'):
                abort = True
            if abort:
                print >>sys.stderr, "[CLAM Dispatcher] ABORTING PROCESS ON SIGNAL! (" + str(d)+"s)"
                running = True
                while running:
                    os.system("kill -15 " + str(pid))
                    running = (os.system('ps ' + str(pid)) == 0)
                    if running:
                        idle += 0.2
                        time.sleep(0.2)
                os.unlink(projectdir + '.abort')
                break
        if d <= 1:
            idle += 0.05
            time.sleep(0.05)
        elif d <= 2:
            idle += 0.2
            time.sleep(0.2)
        elif d <= 10:
            idle += 0.5
            time.sleep(0.5)
        else:
            idle += 1
            time.sleep(1)

        if settings.DISPATCHER_MAXRESMEM > 0 and total_seconds(datetime.datetime.now() - lastpolltime) >= settings.DISPATCHER_POLLINTERVAL:
            resmem = mem(pid)
            if resmem > settings.DISPATCHER_MAXRESMEM * 1024:
                print >>sys.stderr, "[CLAM Dispatcher] PROCESS EXCEEDS MAXIMUM RESIDENT MEMORY USAGE (" + str(resmem) + ' >= ' + str(settings.DISPATCHER_MAXRESMEM) + ')... ABORTING'
                abort = True
                abortchecktime = lastpolltime
                statuscode = 2
            lastpolltime = datetime.datetime.now()
        elif settings.DISPATCHER_MAXTIME > 0 and d > settings.DISPATCHER_MAXTIME:
            print >>sys.stderr, "[CLAM Dispatcher] PROCESS TIMED OUT.. NO COMPLETION WITHIN " + str(d) + " SECONDS ... ABORTING"
            abort = True
            statuscode = 3

    f = open(projectdir + '.done','w')
    f.write(str(statuscode))
    f.close()
    if os.path.exists(projectdir + '.pid'): os.unlink(projectdir + '.pid')

    d = total_seconds(datetime.datetime.now() - begintime)
    print >>sys.stderr, "[CLAM Dispatcher] Finished (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "), exit code " + str(statuscode) + ", dispatcher wait time " + str(idle)  + "s, duration " + str(d) + "s"

    return statuscode

if __name__ == '__main__':
    sys.exit(main())
