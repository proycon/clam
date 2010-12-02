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

import sys
import os
sys.path.append(sys.path[0] + '/..')
os.environ['PYTHONPATH'] = sys.path[0] + '/..'


from clam.common.client import CLAMClient, NotFound, PermissionDenied, ServerError, AuthRequired
from clam.common.data import ParameterCondition

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
    #print >>sys.stderr, " download [project] [filename]"
    #print >>sys.stderr, "\t Download the specified output file (with metadata)"
    print >>sys.stderr, " upload   [project] [inputtempate] [file] [[metadata]]"
    print >>sys.stderr, "\t Upload the specified file from client to server. Metadata is either"
    print >>sys.stderr, "\t a file, or a space-sperated set of --key=value parameters."
    print >>sys.stderr, " inputtemplate [inputtemplate]"
    print >>sys.stderr, "\t View the metadata parameters in the requested inputtemplate"
    #print >>sys.stderr, " metadata [project] [filename]"
    #print >>sys.stderr, "\t View the metadata of the specified file"
    


if __name__ == "__main__":
    
    username = password = None
    
    parameters = {}
    begin = 0
    rawargs = sys.argv[1:]
    for i,o in enumerate(rawargs):
        if o == '-u':
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
        elif o[:2] == '--':
            if len(rawargs) > i + 1:
                parameters[o[2:]] = rawargs[i+1]
                begin = i+2
            else:
                parameters[o[2:]] = True
                begin = i+1
    
    if len(rawargs) > begin:
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

    if len(rawargs) > begin + 1:    
        command = rawargs[begin+1]
        args = rawargs[begin+2:]
    else:
        command = 'info'
        args = []
    
    if command == 'info' and len(args) > 1:
        command = 'get'

    
    try:        
        if command in ['info','index','projects','inputtemplates','parameters','profiles']:
            data = client.index()
        elif command in ['get','input','output','status','inputtemplate']:
            if len(args) != 1:
                print >>sys.stderr, "Expected project ID"
                sys.exit(2)
            data = client.get(args[0])
        elif command == 'create':
            if len(args) != 1:
                print >>sys.stderr, "Expected project ID"
                sys.exit(2)
            client.create(args[0])
        elif command == 'delete' or command == 'abort':
            if len(args) != 1:
                print >>sys.stderr, "Expected project ID"
                sys.exit(2)            
            client.delete(args[0])
        elif command == 'reset':
            if len(args) != 1:
                print >>sys.stderr, "Expected project ID"
                sys.exit(2)
            client.reset(args[0])
        elif command == 'xml':
            if len(args) ==1:
                data = client.get(args[0])
            else:
                data = client.index()
        elif command == 'upload':
            if len(args) < 3:
                print >>sys.stderr, "Expected: project inputtemplate file "
                sys.exit(2)        
            data = client.get(args[0])
            try:
                inputtemplate = data.inputtemplate(args[1])
            except:
                print >>sys.stderr, "No such input template: " + args[1]
                sys.exit(2)
            filepath = args[2]
            if not os.path.isfile(filepath):
                print >>sys.stderr, "File does not exist: " + filepath
                sys.exit(2)
            client.upload(project,inputtemplate, filepath, **parameters)                            
        else:
            print >>sys.stderr,"Unknown command: " + command
            sys.exit(1)
        
        
        if data:
            if command == 'xml':
                print data.xml
            if command in ['info','get']:
                print "General Information"
                print "\tSystem ID:   " + data.system_id
                print "\tSystem Name: " + data.system_name
                print "\tSystem URL:  " + data.baseurl
                if username:
                    print "\tUser:        " + username
                if command == 'get':
                    print "\tProject:     " + data.project
            if command in ['info','projects','index']: 
                print "Projects"
                for project in data.projects:
                    print "\t" + project
            if command in ['get','status']:
                print "Status Information"
                print "\tStatus: " + str(data.status) #TODO: nicer messages
                print "\tStatus Message: " + data.statusmessage
                print "\tCompletion: " + str(data.completion) + "%"
            if command in ['info','profiles']: 
                print "Profiles:" #TODO: Implement
                for i, profile in enumerate(data.profiles):
                    print "\tProfile " + str(i+1)
                    print "\t Input"
                    for template in profile.input:
                        print "\t\t" + template.id + " - " + template.label
                    print "\t Output"
                    for template in profile.output:
                        if isinstance(template, ParameterCondition):
                            for t in template.allpossibilities():
                                print "\t\t(CONDITIONAL!) " + t.id + " - " + t.label
                        else:
                            print "\t\t" + template.id + " - " + template.label
            if command == 'inputtemplates':
                print "Input templates:"
                for template in data.input:
                    print "\t\t" + template.id + " - " + template.label            
            if command == 'inputtemplate':
                try:
                    inputtemplate = data.inputtemplate(args[0])
                except:
                    print >>sys.stderr, "No such inputtemplate"                
                    sys.exit(1)
                print "Inputtemplate parameters:"
                for parameter in inputtemplate.parameters:
                    print "\t\t" + str(parameter) #VERIFY: unicode support?
                print "Inputtemplate converters:"
                for c in inputtemplate.converters:
                    print "\t\t" + c.id + " - " + c.label #VERIFY: unicode support?
            if command in ['info','parameters']: 
                print "Global Parameters:"
                for group, parameters in data.parameters:
                    print "\t" + group
                    for parameter in parameters:
                        print "\t\t" + str(parameter) #VERIFY: unicode support?
            if command in ['get','input'] and data.input: 
                print "Input files:"
                for f in data.input:
                    print "\t" + f.filename + "\t" + str(f),
                    if f.metadata and f.metadata.inputtemplate:
                        print "\t" + f.metadata.inputtemplate
                    else:
                        print
            if command in ['get','output'] and data.output: 
                print "Output files:"
                for f in data.output:
                    print "\t" + f.filename + "\t" + str(f), 
                    if f.metadata and f.metadata.provenance and f.metadata.provenance.outputtemplate_id:
                        print "\t" + f.metadata.provenance.outputtemplate_id
                    else:
                        print 

    except NotFound: 
        print >>sys.stderr, "Not Found (404)"
    except PermissionDenied: 
        print >>sys.stderr, "Permission Denied (403)"
    except ServerError: 
        print >>sys.stderr, "Server Error! (500)"
    except AuthRequired: 
        print >>sys.stderr, "Authorization required (401)"      
        

