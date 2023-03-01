#!/usr/bin/env python3
#-*- coding:utf-8 -*-


###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Dispatcher --
#       by Maarten van Gompel (proycon)
#
#       Licensed under GPLv3
###############################################################

import sys
import os
import datetime
import subprocess
import time
import signal
import shutil
import json

VERSION = '3.2.5'

sys.path.append(sys.path[0] + '/..')

import clam.common.data #pylint: disable=wrong-import-position
import clam.common.status
from clam.common.util import computediskusage


def mem(pid, size="rss"):
    """memory sizes: rss, rsz, vsz."""
    return int(os.popen('ps -p %d -o %s | tail -1' % (pid, size)).read())

def total_seconds(delta):
    return delta.days * 86400 + delta.seconds + (delta.microseconds / 1000000.0)

def updateindex(projectpath):
    """Update the index"""
    totalsize = 0.0
    if os.path.exists(os.path.join(projectpath,'..','.index')):
        with open(os.path.join(projectpath,'..','.index'),'r',encoding='utf-8') as f:
            try:
                data = json.load(f)
            except ValueError:
                #delete the entire index
                os.unlink(os.path.join(projectpath,'..','.index'))
                return False
    else:
        data = {"projects": [], 'totalsize': 0.0}
    if not os.path.isdir(projectpath):
        return False
    d = datetime.datetime.fromtimestamp(os.stat(projectpath)[8])
    project = os.path.basename(projectpath.rstrip('/'))
    projectsize, filecount = computediskusage(projectpath)
    with open(os.path.join(projectpath,'.du'),'w') as f:
        f.write(str(projectsize) + "\n")
        f.write(str(filecount))
    index = None
    for i, projectdata in enumerate(data['projects']):
        if projectdata[0] == project:
            index = i
        else:
            totalsize += projectdata[2]
    projectdata = ( project , d.strftime("%Y-%m-%d %H:%M:%S"), round(projectsize,2), clam.common.status.DONE )
    changed = True
    if index is None:
        data['projects'].append(  projectdata   )
        data["totalsize"] = totalsize + projectsize
    elif data["projects"][index] != projectdata:
        data["projects"][index] = projectdata
        data["totalsize"] = totalsize + projectsize
    else:
        changed = False
        if totalsize != data['totalsize']:
            data["totalsize"] = totalsize
            changed = True
    if changed:
        with open(os.path.join(projectpath,'..','.index'),'w',encoding='utf-8') as f:
            json.dump(data,f, ensure_ascii=False)
    return True

def main():
    if len(sys.argv) < 4:
        print("[CLAM Dispatcher] ERROR: Invalid syntax, use clamdispatcher.py [pythonpath] settingsmodule projectdir cmd arg1 arg2 ... got: " + " ".join(sys.argv[1:]), file=sys.stderr)
        with open('.done','w') as f:
            f.write(str(1))
        if os.path.exists('.pid'): os.unlink('.pid')
        return 1

    offset = 0
    if '/' in sys.argv[1]:
        #os.environ['PYTHONPATH'] = sys.argv[1]
        for path in sys.argv[1].split(':'):
            print("[CLAM Dispatcher] Adding to PYTHONPATH: " + path, file=sys.stderr)
            sys.path.append(path)
        offset = 1

    settingsmodule = sys.argv[1+offset]
    projectdir = sys.argv[2+offset]
    if projectdir == 'NONE': #Actions
        tmpdir = None
        projectdir = None
    elif projectdir.startswith('tmp://'): #Used for actions with a temporary dir
        tmpdir = projectdir[6:]
        projectdir = None
    else:
        if projectdir[-1] != '/':
            projectdir += '/'
        tmpdir = os.path.join(projectdir,'tmp')

    print("[CLAM Dispatcher] Started CLAM Dispatcher v" + str(VERSION) + " with " + settingsmodule + " (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ")", file=sys.stderr)

    cmd = sys.argv[3+offset]
    cmd = clam.common.data.unescapeshelloperators(cmd) #shell operators like pipes and redirects were passed in an escaped form
    for arg in sys.argv[4+offset:]:
        arg_u = clam.common.data.unescapeshelloperators(arg)
        if arg_u != arg:
            cmd += " " + arg_u #shell operator (pipe or something)
        else:
            cmd += " " + clam.common.data.shellsafe(arg,'"')


    if not cmd:
        print("[CLAM Dispatcher] FATAL ERROR: No command specified!", file=sys.stderr)
        if projectdir:
            f = open(projectdir + '.done','w')
            f.write(str(1))
            f.close()
            if os.path.exists(projectdir + '.pid'): os.unlink(projectdir + '.pid')
        return 1
    elif projectdir and not os.path.isdir(projectdir):
        print("[CLAM Dispatcher] FATAL ERROR: Project directory "+ projectdir + " does not exist", file=sys.stderr)
        return 1

    try:
        #exec("import " + settingsmodule + " as settings")
        settings = __import__(settingsmodule , globals(), locals(),0)
        try:
            if settings.CUSTOM_FORMATS:
                clam.common.data.CUSTOM_FORMATS = settings.CUSTOM_FORMATS
                print("[CLAM Dispatcher] Dependency injection for custom formats succeeded", file=sys.stderr)
        except AttributeError:
            pass
    except ImportError as e:
        print("[CLAM Dispatcher] FATAL ERROR: Unable to import settings module, settingsmodule is " + settingsmodule + ", error: " + str(e), file=sys.stderr)
        print("[CLAM Dispatcher]      hint: If you're using the development server, check you pass the path your service configuration file is in using the -P flag. For Apache integration, verify you add this path to your PYTHONPATH (can be done from the WSGI script)", file=sys.stderr)
        if projectdir:
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


    try:
        print("[CLAM Dispatcher] Running " + cmd, file=sys.stderr)
    except (UnicodeDecodeError, UnicodeError, UnicodeEncodeError):
        print("[CLAM Dispatcher] Running " + repr(cmd), file=sys.stderr) #unicode-issues on Python 2

    if projectdir:
        process = subprocess.Popen(cmd,cwd=projectdir, shell=True, stderr=sys.stderr)
    else:
        process = subprocess.Popen(cmd, shell=True, stderr=sys.stderr)
    begintime = datetime.datetime.now()
    if process:
        pid = process.pid
        print("[CLAM Dispatcher] Running with pid " + str(pid) + " (" + begintime.strftime('%Y-%m-%d %H:%M:%S') + ")", file=sys.stderr)
        sys.stderr.flush()
        if projectdir:
            with open(projectdir + '.pid','w') as f:
                f.write(str(pid))
    else:
        print("[CLAM Dispatcher] Unable to launch process", file=sys.stderr)
        sys.stderr.flush()
        if projectdir:
            with open(projectdir + '.done','w') as f:
                f.write(str(1))
        return 1

    #intervalf = lambda s: min(s/10.0, 15)
    abort = False
    idle = 0
    done = False
    lastpolltime = datetime.datetime.now()
    lastabortchecktime = datetime.datetime.now()

    while not done:
        d = total_seconds(datetime.datetime.now() - begintime)
        try:
            returnedpid, statuscode = os.waitpid(pid, os.WNOHANG)
            if returnedpid != 0:
                print("[CLAM Dispatcher] Process ended (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ", " + str(d)+"s) ", file=sys.stderr)
                done = True
        except OSError: #no such process
            print("[CLAM Dispatcher] Process lost! (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ", " + str(d)+"s)", file=sys.stderr)
            statuscode = 1
            done = True

        if done:
            break

        if total_seconds(datetime.datetime.now() - lastabortchecktime) >= min(10, d* 0.5):  #every 10 seconds, faster at beginning
            if projectdir and os.path.exists(projectdir + '.abort'):
                abort = True
            if abort:
                print("[CLAM Dispatcher] ABORTING PROCESS ON SIGNAL! (" + str(d)+"s)", file=sys.stderr)
                os.system("sleep 30 && kill -9 " + str(pid) + " &") #deathtrap in case the process doesn't listen within 30 seconds
                os.kill(pid, signal.SIGTERM)
                os.waitpid(pid, 0)
                if projectdir:
                    os.unlink(projectdir + '.abort')
                    open(projectdir + '.aborted','w')
                    f.close()
                done = True
                break
            lastabortchecktime = datetime.datetime.now()


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
                print("[CLAM Dispatcher] PROCESS EXCEEDS MAXIMUM RESIDENT MEMORY USAGE (" + str(resmem) + ' >= ' + str(settings.DISPATCHER_MAXRESMEM) + ')... ABORTING', file=sys.stderr)
                abort = True
                statuscode = 2
            lastpolltime = datetime.datetime.now()
        elif settings.DISPATCHER_MAXTIME > 0 and d > settings.DISPATCHER_MAXTIME:
            print("[CLAM Dispatcher] PROCESS TIMED OUT.. NO COMPLETION WITHIN " + str(d) + " SECONDS ... ABORTING", file=sys.stderr)
            abort = True
            statuscode = 3

    if projectdir:
        with open(projectdir + '.done','w') as f:
            f.write(str(statuscode))
        if os.path.exists(projectdir + '.pid'): os.unlink(projectdir + '.pid')

        #update project index cache
        print("[CLAM Dispatcher] Updating project index", file=sys.stderr)
        updateindex(projectdir)


    if tmpdir and os.path.exists(tmpdir):
        print("[CLAM Dispatcher] Removing temporary files", file=sys.stderr)
        for filename in os.listdir(tmpdir):
            filepath = os.path.join(tmpdir,filename)
            try:
                if os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                else:
                    os.unlink(filepath)
            except: #pylint: disable=bare-except
                print("[CLAM Dispatcher] Unable to remove " + filename, file=sys.stderr)

    d = total_seconds(datetime.datetime.now() - begintime)
    if statuscode > 127:
        print("[CLAM Dispatcher] Status code out of range (" + str(statuscode) + "), setting to 127", file=sys.stderr)
        statuscode = 127
    print("[CLAM Dispatcher] Finished (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "), exit code " + str(statuscode) + ", dispatcher wait time " + str(idle)  + "s, duration " + str(d) + "s", file=sys.stderr)

    return statuscode

if __name__ == '__main__':
    sys.exit(main())
