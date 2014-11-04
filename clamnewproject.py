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

import sys
import os
import codecs
import shutil

try:
    import clam
except ImportError:
    print >>sys.stderr, "ERROR: Unable to find CLAM. Either something went wrong during installation or you did not install CLAM globally and are in a directory from which it can not be accessed."
    sys.exit(2)

import getopt

def usage():
        print >> sys.stderr, "Syntax: clamnewproject.py system_id [options]"
        print >> sys.stderr, "Description: This tool sets up a new CLAM project for you. Replace 'system_id' with a short ID/name for your project, this ID is for internal use only and will be used in various filenames, no spaces or other special characters allowed."
        print >> sys.stderr, "Options:"
        print >> sys.stderr, "\t-d [dir]      - Directory prefix, rather than in current working directory"
        print >> sys.stderr, "\t-f            - Force use of a directory that already exists"
        print >> sys.stderr, "\t-h            - This help message"
        print >> sys.stderr, "Configuration shortcuts:"
        print >> sys.stderr, "\t-n [name]     - A human-readable name. Shortcut option, can be also set in service configuration file later."
        print >> sys.stderr, "\t-H [hostname] - Hostname. Shortcut option, can be also set in service configuration file later. "
        print >> sys.stderr, "\t-p [port]     - Port.  Shortcut option, can be also set in service configuration file later."
        print >> sys.stderr, "\t-u [url]      - Force URL. Shortcut option, can be also set in service configuration file later."


def main():
    if len(sys.argv) < 2 or sys.argv[1][0] == '-':
        usage()
        sys.exit(1)

    sysid = sys.argv[1]
    if ' ' in sysid or '.' in sysid or '-' in sysid or ',' in sysid or ':' in sysid or ':' in sysid or '(' in sysid or ')' in sysid or '/' in sysid or "'" in sysid or '"' in sysid:
        print >>sys.stderr, "Invalid characters in system ID. Only alphanumerics and underscores are allowed."
        sys.exit(2)


    HOST = FORCEURL = None
    PORT = 8080
    dirprefix = os.getcwd()
    force = False
    name = ""

    try:
        opts, args = getopt.getopt(sys.argv[2:], "hd:cH:p:u:fn:")
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err)
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
            print "ERROR: Unknown option: ", o
            sys.exit(2)



    clampath = clam.__path__[0]

    if not os.path.exists(clampath + '/config/template.py') or not os.path.exists(clampath + '/wrappers/template.py'):
        print >>sys.stderr, "ERROR: Templates not found. Unable to create new project"
        sys.exit(2)

    dir = dirprefix + "/" +sysid

    if os.path.exists(dir):
        if not force:
            print >>sys.stderr, "ERROR: Directory " +dir + " already exists.. Unable to make new CLAM project. Add -f (force) if you want to continue nevertheless "
            sys.exit(2)
    else:
        print >>sys.stderr, "Making project directory " + dir
        os.mkdir(dir)

    if not os.path.exists(dir+ "/__init__.py"):
        f = open(dir+ "/__init__.py",'w')
        f.close()

    if not os.path.exists(dir + '/' + sysid + '.py'):
        fin = codecs.open(clampath + '/config/template.py','r','utf-8')
        fout = codecs.open(dir + '/' + sysid + '.py','w','utf-8')
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
                line = "COMMAND = \"" + dir + "/" + sysid + "-wrapper.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY\"\n"
            fout.write(line)
        fin.close()
        fout.close()
    else:
        print >>sys.stderr, "WARNING: Service configuration file " + dir + '/' + sysid + ".py already seems to exists, courageously refusing to overwrite"
        sys.exit(2)

    if not os.path.exists(dir + '/' + sysid + '-wrapper.py'):
        shutil.copyfile(clampath + '/wrappers/template.py', dir + '/' + sysid + '-wrapper.py')
        os.chmod(dir + '/' + sysid + '-wrapper.py', 0755)
    else:
        print >>sys.stderr, "WARNING: System wrapper file " + dir + '/' + sysid + '-wrapper.py already seems to exists, defiantly refusing to overwrite'
        sys.exit(2)

    s = "Your new CLAM project has been set up!\n"
    s += "WHAT'S NEXT? Now you can edit your service configuration file " +  dir + '/' + sysid + ".py and your system wrapper script " +   dir + '/' + sysid + "-wrapper.py . Consult the CLAM Documentation and/or instruction videos on http://proycon.github.com/clam for further details.\n\n"

    print >>sys.stderr, s

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

    s2 = "STARTING CLAM? Whilst you are in the process of building your CLAM webservice, you can start and test your webservice using the built-in development webserver: $ clamservice -P " + dirprefix + "/" + sysid + ' ' + sysid , " after which you can point your browser or CLAM client to " + url + ".\n\n"
    print >>sys.stderr, s2

    print >>sys.stderr, "All of this information can be read in the " + dir + "/INSTRUCTIONS file"

    with open(dir + "/INSTRUCTIONS",'w') as f:
        f.write(s + s2)



if __name__ == "__main__":
    main()
