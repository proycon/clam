#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Generic CLAM Client --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
# This is a very generic CLAM command-line client, useable with 
# any CLAM Service. It provides a simple and fairly low-level
# command-line interface.
#
###############################################################

from clam.common.client import CLAMClient, NotFound, PermissionDenied, 

import getopt
import sys

VERSION = '0.5'

def usage():
    print >>sys.stderr, "clamclient.py [[options]] [url] [command] [command-arguments]"
    print >>sys.stderr, "  Low-level command-line interface to any CLAM webservice"
    print >>sys.stderr, "Options:"
    print >>sys.stderr, "\t-u [username]"
    print >>sys.stderr, "\t-p [password]"
    print >>sys.stderr, "\t-x              - Output CLAM XML, instead of an interpretation thereof"
    print >>sys.stderr, "\t-h              - Help"
    print >>sys.stderr, "\t-v              - Version information"
    print >>sys.stderr, "Commands:"
    print >>sys.stderr, " info             - Get service specification and project list (returns raw CLAM XML), this is the default if no command is specified."
    print >>sys.stderr, " projects         - Show a list of available projects"
    #print >>sys.stderr, "profiles         - Render an overview of all profiles"
    print >>sys.stderr, " inputtemplates   - Show a list of all available input templates and their metadata"
    print >>sys.stderr, " parameters       - Render an overview of all global parameters"
    print >>sys.stderr, " create [project] - Create a new empty project with the specified ID"
    print >>sys.stderr, " delete [project] - Delete the specified project (aborts any run)"
    print >>sys.stderr, " reset  [project] - Delete a project's output and reset"
    print >>sys.stderr, " get    [project] - Get project "
    print >>sys.stderr, " download [project] [filename]"
    print >>sys.stderr, "\t Download the specified output file"
    print >>sys.stderr, " upload   [project] [inputtempate] [file] [[metadata]]"
    print >>sys.stderr, "\t Upload the specified file from client to server. Metadata is either"
    print >>sys.stderr, "\t a file, or a space-sperated set of --key=value parameters."



if __name__ == "__main__":
    
    xmloutput = False
    username = password = None
    
    begin = 0
    rawargs = sys.argv[1:]
    for i,o in enumerate(rawargs]
        elif o == '-u':
            username = rawargs[i+1]
            begin = i+2
        elif o == '-p':
            password = rawargs[i+1]
            begin = i+2
        elif o == '-h':
            usage()
            sys.exit(0)
        elif o == '-v':
            print "CLAM Client version " + str(VERSION)
            sys.exit(0)
        elif o == '-x':
            xmloutput = True
            begin = i + 1
        elif o[0] == '-' and len(o) > 1 and o[1] != '-':
            usage()
            print "ERROR: Unknown option: ", o
            sys.exit(2)            
    
    if not len(rawargs) > begin:
        url = rawargs[begin]
    else:
        usage()
        sys.exit(2)
        print "ERROR: URL expected"
    if url[:4] != 'http':
        print "ERROR: URL expected"
        usage()
        sys.exit(2)
    
    client = CLAMClient(url, username,password)

    if not len(rawargs) > begin + 1:    
        command = rawargs[begin+1]
        args = rawargs[begin+2:]
    else:
        command = 'info'
        args = []
    
    try:        
        if command == 'info':
            data = client.index()
            
        elif command == 'projects':
            data = client.index()                
            for project in data.projects:
                print project        
        else:
            print "ERROR: No such command: " + command
        

    except: 
        

