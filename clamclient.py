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
    print >>sys.stderr, "\t-h              - Help"
    print >>sys.stderr, "\t-v              - Version information"
    print >>sys.stderr, "Commands:"
    print >>sys.stderr, " info             - Get service specification and project list, this is the default if no command is specified."
    print >>sys.stderr, " projects         - Show a list of available projects"
    print >>sys.stderr, " profiles         - Render an overview of all profiles"
    print >>sys.stderr, " inputtemplates   - Show a list of all available input templates and their metadata"
    print >>sys.stderr, " parameters       - Render an overview of all global parameters"
    print >>sys.stderr, " info   [project] - Get all info of a project, including full service specification "
    print >>sys.stderr, " create [project] - Create a new empty project with the specified ID"
    print >>sys.stderr, " delete [project] - Delete the specified project (aborts any run)"
    print >>sys.stderr, " reset  [project] - Delete a project's output and reset"
    print >>sys.stderr, " status [project] - Get a project's status"
    print >>sys.stderr, " input  [project] - Get a list of input files"
    print >>sys.stderr, " output [project] - Get a list of output files"
    print >>sys.stderr, " xml              - Get service specification and project list in CLAM XML"
    print >>sys.stderr, " xml    [project] - Get entire project state in CLAM XML"        
    print >>sys.stderr, " download [project] [filename]"
    print >>sys.stderr, "\t Download the specified output file (with metadata)"
    print >>sys.stderr, " upload   [project] [inputtempate] [file] [[metadata]]"
    print >>sys.stderr, "\t Upload the specified file from client to server. Metadata is either"
    print >>sys.stderr, " metadata [project] [filename]"
    print >>sys.stderr, "\t View the metadata of the specified file"
    print >>sys.stderr, "\t a file, or a space-sperated set of --key=value parameters."



if __name__ == "__main__":
    
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
    
    if command == 'info' and len(args) > 1:
        command = 'get'

    

    
    try:        
        if command in ['info','projects','inputtemplates','parameters']:
            data = client.index()
        elif command in ['get','input','output','status']:
            data = client.project(args[0])
        elif command == 'create':
            client.create(args[0])
        elif command == 'delete' or command == 'abort':
            client.delete(args[0])
        elif command == 'reset':
            client.reset(args[0])
        else:
            data = None
        

        if data:
            if outputxml:
            else:   
                if command == 'xml':
                    print data.xml()
                if command in ['info','get']:
                    print "General Information"
                    print "\tSystem ID:   " + data.system_id
                    print "\tSystem Name: " + data.system_name
                    print "\tSystem URL:  " + data.baseurl
                    if user:
                        print "\tUser:        " + user
                    if command == 'get':
                        print "\tProject:     " + data.project
                if command in ['info','projects']: 
                    print "Projects"
                    for project in data.projects:
                        print "\t" + project
                if command in ['info','status']:
                    print "Status Information"
                    print "\tStatus: " + str(data.status) #TODO: nicer messages
                    print "\tStatus Message: " + data.statusmessage
                    print "\tCompletion: " + str(data.completion) + "%"
                if command in ['info','profiles']: 
                    print "Profiles:" #TODO: Implement
                if command in ['info','parameters']: 
                    print "Global Parameters:"
                    for group, parameters in data.parameters:
                        print "\t" + group
                        for parameter in parameters:
                            print "\t\t" + str(parameter) #VERIFY: unicode support?
                if command in ['get','input'] and data.input: 
                    print "Input files:"
                    for f in data.input:
                        print f.filename + "\t" + str(f),
                        if f.metadata and f.metadata.inputtemplate:
                            print "\t" + f.metadata.inputtemplate
                        else:
                            print
                if command in ['get','output'] and data.input: 
                    print "Output files:"
                    for f in data.output:
                        print f.filename + "\t" + str(f), 
                        if f.metadata and f.metadata.provenance and f.metadata.provenance.outputtemplate_id:
                            print "\t" + f.metadata.provenance.outputtemplate_id
                        else:
                            print 
                
                

    except: 
        

