#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os
import datetime
import subprocess

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
process = subprocess.Popen(cmd,cwd=projectdir, shell=True, stdout=stdout)				
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
    
returnedpid, statuscode = os.wait() #waitpid(pid)

f = open(projectdir + '.done','w')
f.write(str(statuscode))
f.close()
os.unlink(projectdir + '.pid')

    
print >>sys.stderr, "[CLAM Dispatcher] Finished (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "), exit code " + str(statuscode)

sys.exit(statuscode)
