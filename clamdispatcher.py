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

VERSION = '0.6.0'

sys.path.append(sys.path[0] + '/..')
os.environ['PYTHONPATH'] = sys.path[0] + '/..'

if len(sys.argv) < 4:
    print >>sys.stderr,"[CLAM Dispatcher] ERROR: Invalid syntax, use clamdispatcher.py settingsmodule projectdir cmd arg1 arg2 ..."
    sys.exit(1)

settingsmodule = sys.argv[1]
projectdir = sys.argv[2]
if projectdir[-1] != '/':
    projectdir += '/'

cmd = " ".join(sys.argv[3:])

print >>sys.stderr, "[CLAM Dispatcher] Started (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ")"

if not cmd:
    print >>sys.stderr, "[CLAM Dispatcher] FATAL ERROR: No command specified!"
    sys.exit(1)
elif not os.path.isdir(projectdir):
    print >>sys.stderr, "[CLAM Dispatcher] FATAL ERROR: Project directory "+ projectdir + " does not exist"
    sys.exit(1)

exec "import " + settingsmodule + " as settings"
settingkeys = dir(settings)

print >>sys.stderr, "[CLAM Dispatcher] Running " + cmd

process = subprocess.Popen(cmd,cwd=projectdir, shell=True, stderr=sys.stderr)				
begintime = datetime.datetime.now()
if process:
    pid = process.pid
    print >>sys.stderr, "[CLAM Dispatcher] Running with pid " + str(pid)
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
    sys.exit(1)
    
#intervalf = lambda s: min(s/10.0, 15)
abortchecktime = 0
idle = 0
done = False

while not done:    
    duration = datetime.datetime.now() - begintime
    d = duration.microseconds / 1000000.0    
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
            print >>sys.stderr, "[CLAM Dispatcher] ABORTING PROCESS ON USER SIGNAL! (" + str(d)+"s)"
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
    
f = open(projectdir + '.done','w')
f.write(str(statuscode))
f.close()
os.unlink(projectdir + '.pid')

d = duration.microseconds / 1000000.0  
print >>sys.stderr, "[CLAM Dispatcher] Finished (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "), exit code " + str(statuscode) + ", dispatcher wait time " + str(idle)  + "s, duration " + str(d) + "s"
 
sys.exit(statuscode)
