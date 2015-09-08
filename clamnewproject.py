#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Webservice --
#       by Maarten van Gompel (proycon)
#       http://proycon.github.com/clam
#
#       Centre for Language Studies
#       Radboud University Nijmegen
#
#       Induction for Linguistic Knowledge Research Group
#       Tilburg University
#
#       Licensed under GPLv3
#
###############################################################


from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import io
import shutil

try:
    import clam
except ImportError:
    print("ERROR: Unable to find CLAM. Either something went wrong during installation or you did not install CLAM globally and are in a directory from which it can not be accessed.",file=sys.stderr)
    sys.exit(2)

import getopt

def usage():
        print("Syntax: clamnewproject.py system_id [options]",file=sys.stderr)
        print("Description: This tool sets up a new CLAM project for you. Replace 'system_id' with a short ID/name for your project, this ID is for internal use only and will be used in various filenames, no spaces or other special characters allowed.",file=sys.stderr)
        print("Options:",file=sys.stderr)
        print("\t-d [dir]      - Directory prefix, rather than in current working directory",file=sys.stderr)
        print("\t-f            - Force use of a directory that already exists",file=sys.stderr)
        print("\t-h            - This help message",file=sys.stderr)
        print("Configuration shortcuts:",file=sys.stderr)
        print("\t-n [name]     - A human-readable name. Shortcut option, can be also set in service configuration file later.",file=sys.stderr)
        print("\t-H [hostname] - Hostname. Shortcut option, can be also set in service configuration file later. ",file=sys.stderr)
        print("\t-p [port]     - Port.  Shortcut option, can be also set in service configuration file later.",file=sys.stderr)
        print("\t-u [url]      - Force URL. Shortcut option, can be also set in service configuration file later.",file=sys.stderr)


def main():
    if len(sys.argv) < 2 or sys.argv[1][0] == '-':
        usage()
        sys.exit(1)

    sysid = sys.argv[1]
    if ' ' in sysid or '.' in sysid or '-' in sysid or ',' in sysid or ':' in sysid or ':' in sysid or '(' in sysid or ')' in sysid or '/' in sysid or "'" in sysid or '"' in sysid:
        print("Invalid characters in system ID. Only alphanumerics and underscores are allowed.",file=sys.stderr)
        sys.exit(2)


    HOST = FORCEURL = None
    PORT = 8080
    dirprefix = os.getcwd()
    force = False
    name = ""

    try:
        opts, args = getopt.getopt(sys.argv[2:], "hd:cH:p:u:fn:")
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-d':
            dirprefix = a
        elif o == '-H':
            HOST = a
        elif o == '-p':
            PORT = int(a)
        elif o == '-h':
            usage()
            sys.exit(0)
        elif o == '-u':
            FORCEURL = a
        elif o == '-f':
            force = True
        elif o == '-n':
            name = a
        else:
            usage()
            print("ERROR: Unknown option: ", o)
            sys.exit(2)



    clampath = clam.__path__[0]

    if not os.path.exists(clampath + '/config/template.py') or not os.path.exists(clampath + '/wrappers/template.py'):
        print("ERROR: Templates not found. Unable to create new project",file=sys.stderr)
        sys.exit(2)

    dir = dirprefix + "/" +sysid

    if os.path.exists(dir):
        if not force:
            print("ERROR: Directory " +dir + " already exists.. Unable to make new CLAM project. Add -f (force) if you want to continue nevertheless ",file=sys.stderr)
            sys.exit(2)
    else:
        print("Making project directory " + dir,file=sys.stderr)
        os.mkdir(dir)

    if not os.path.exists(dir+ "/__init__.py"):
        f = open(dir+ "/__init__.py",'w')
        f.close()

    if not os.path.exists(dir + '/' + sysid + '.py'):
        fin = io.open(clampath + '/config/template.py','r',encoding='utf-8')
        fout = io.open(dir + '/' + sysid + '.py','w',encoding='utf-8')
        for line in fin:
            if line == "SYSTEM_ID = \"\"\n":
                line =  "SYSTEM_ID = \"" + sysid + "\""
            elif name and line[:13] == "SYSTEM_NAME =":
                line = "SYSTEM_NAME = \"" + name + "\"\n"
            elif HOST and line[:7] == "#HOST =":
                line = "HOST = \"" + HOST + "\"\n"
            elif PORT and (line[:7] == "#PORT =" or line[:6] == "PORT ="):
                line = "PORT = \"" + str(PORT) + "\"\n"
            elif line[:6] == "ROOT =":
                line = "ROOT = \"" + dir + "/userdata\"\n"
            elif line[:10] == "#CLAMDIR =":
                clamdir = os.path.dirname(clam.__file__)
                line = "#CLAMDIR = \"" + clamdir + "\" #(automatically detected)\n"
            elif FORCEURL and line[:9] == '#FORCEURL':
                line = "FORCEURL = \"" + FORCEURL + "\"\n"
            elif line[:9] == "COMMAND =":
                line = "COMMAND = \"" + dir + "/" + sysid + "_wrapper.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY\"\n"
            fout.write(line)
        fin.close()
        fout.close()
    else:
        print("WARNING: Service configuration file " + dir + '/' + sysid + ".py already seems to exists, courageously refusing to overwrite",file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(dir + '/' + sysid + '_wrapper.py'):
        shutil.copyfile(clampath + '/wrappers/template.py', dir + '/' + sysid + '_wrapper.py')
        os.chmod(dir + '/' + sysid + '_wrapper.py', 0o755)
    else:
        print("WARNING: System wrapper file " + dir + '/' + sysid + 'wrapper.py already seems to exists, defiantly refusing to overwrite',file=sys.stderr)
        sys.exit(2)

    s = "Your new CLAM project has been set up!\n\n"
    s += "WHAT'S NEXT?\n Now you can edit your service configuration file " +  dir + '/' + sysid + ".py,\nand your system wrapper script " +   dir + '/' + sysid + "-wrapper.py .\nConsult the CLAM Documentation and/or instruction videos on https://proycon.github.io/clam for further details.\n\n"

    print(s,file=sys.stderr)

    if FORCEURL:
        url = FORCEURL
    else:
        url = "http://"
        if HOST:
            url += HOST
        else:
            url += os.uname()[1]
        if PORT and PORT != 80:
            url += ':' + str(PORT)
        url += '/'

    s2 = "STARTING CLAM?\nWhilst you are in the process of building your CLAM webservice, \nyou can start and test your webservice using the built-in development webserver:\n $ clamservice -P " + dirprefix + "/" + sysid + ' ' + sysid + "\nafter which you can point your browser or CLAM client to:\n" + url + ".\n\n"
    print( s2,file=sys.stderr)

    print( "All of this information can be read in the " + dir + "/INSTRUCTIONS file",file=sys.stderr)

    with io.open(dir + "/INSTRUCTIONS",'w',encoding='utf-8') as f:
        f.write(s + s2)



if __name__ == "__main__":
    main()
