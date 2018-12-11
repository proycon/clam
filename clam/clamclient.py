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

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
sys.path.append(sys.path[0] + '/..')
os.environ['PYTHONPATH'] = sys.path[0] + '/..'


from clam.common.client import CLAMClient
from clam.common.data import ParameterCondition, NotFound, PermissionDenied, ServerError, AuthRequired

VERSION = '2.0'

def usage():
    print("clamclient.py [[options]] [url] [command] [command-arguments]",file=sys.stderr)
    print("  Low-level command-line interface to any CLAM webservice",file=sys.stderr)
    print("Options:",file=sys.stderr)
    print("\t-u [username]",file=sys.stderr)
    print("\t-p [password]",file=sys.stderr)
    print("\t-b              - Use HTTP Basic Authentication instead of Digest",file=sys.stderr)
    print("\t-h              - Help",file=sys.stderr)
    print("\t-v              - Version information",file=sys.stderr)
    print("Commands:",file=sys.stderr)
    print(" info             - Get service specification and project list, this is the default if no command is specified.",file=sys.stderr)
    print(" projects         - Show a list of available projects",file=sys.stderr)
    print(" profiles         - Render an overview of all profiles",file=sys.stderr)
    print(" inputtemplates   - Show a list of all available input templates and their metadata",file=sys.stderr)
    print(" parameters       - Render an overview of all global parameters",file=sys.stderr)
    print(" info   [project] - Get all info of a project, including full service specification ",file=sys.stderr)
    print(" create [project] - Create a new empty project with the specified ID",file=sys.stderr)
    print(" delete [project] - Delete the specified project (aborts any run)",file=sys.stderr)
    #prin(" reset  [project] - Delete a project's output and reset",file=sys.stderr)
    print(" start [project]  - Start the project",file=sys.stderr)
    print(" status [project] - Get a project's status",file=sys.stderr)
    print(" input  [project] - Get a list of input files",file=sys.stderr)
    print(" output [project] - Get a list of output files",file=sys.stderr)
    print(" xml              - Get service specification and project list in CLAM XML",file=sys.stderr)
    print(" xml    [project] - Get entire project state in CLAM XML",file=sys.stderr)
    print(" download [project] [filename] [[targetfile]]",file=sys.stderr)
    print("\t Download the specified output file",file=sys.stderr)
    print(" upload   [project] [inputtempate] [file] [[metadata]]",file=sys.stderr)
    print("\t Upload the specified file from client to server. Metadata is either",file=sys.stderr)
    print("\t a file, or a space-sperated set of --key=value parameters.",file=sys.stderr)
    print(" inputtemplate [inputtemplate]",file=sys.stderr)
    print("\t View the metadata parameters in the requested inputtemplate",file=sys.stderr)
    #prin(" metadata [project] [filename]",file=sys.stderr)
    #prin("\t View the metadata of the specified file",file=sys.stderr)



def main():
    username = password = None
    basicauth = False
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
        elif o == '-h':
            basicauth = True
        elif o == '-v':
            print("CLAM Client version " + str(VERSION),file=sys.stderr)
            sys.exit(0)
        elif o[0] == '-' and len(o) > 1 and o[1] != '-':
            usage()
            print("ERROR: Unknown option: ", o,file=sys.stderr)
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
        print("ERROR: URL expected",file=sys.stderr)
    if url[:4] != 'http':
        print("ERROR: URL expected",file=sys.stderr)
        usage()
        sys.exit(2)

    client = CLAMClient(url, username,password, basicauth=basicauth)

    if len(rawargs) > begin + 1:
        command = rawargs[begin+1]
        args = rawargs[begin+2:]
    else:
        command = 'info'
        args = []

    if command == 'info' and len(args) > 1:
        command = 'get'


    try:
        data = None
        if command in ['info','index','projects','inputtemplates','parameters','profiles']:
            data = client.index()
        elif command in ['get','input','output','status','inputtemplate']:
            if len(args) != 1:
                print("Expected project ID",file=sys.stderr)
                sys.exit(2)
            data = client.get(args[0])
        elif command == 'create':
            if len(args) != 1:
                print("Expected project ID",file=sys.stderr)
                sys.exit(2)
            client.create(args[0])
        elif command == 'delete' or command == 'abort':
            if len(args) != 1:
                print("Expected project ID",file=sys.stderr)
                sys.exit(2)
            client.delete(args[0])
        #elif command == 'reset':
        #    if len(args) != 1:
        #        print("Expected project ID"
        #        sys.exit(2)
        #    client.reset(args[0])
        elif command == 'start':
            if len(args) < 1:
                print("Expected project ID",file=sys.stderr)
                sys.exit(2)
            client.start(args[0])
        elif command == 'xml':
            if len(args) ==1:
                data = client.get(args[0])
            else:
                data = client.index()
        elif command == 'upload':
            if len(args) < 3:
                print("Expected: project inputtemplate file ",file=sys.stderr)
                sys.exit(2)
            project = args[0]
            data = client.get(project)
            try:
                inputtemplate = data.inputtemplate(args[1])
            except:
                print("No such input template: " + args[1],file=sys.stderr)
                sys.exit(2)
            filepath = args[2]
            if not os.path.isfile(filepath):
                print("File does not exist: " + filepath,file=sys.stderr)
                sys.exit(2)
            client.upload(project,inputtemplate, filepath, **parameters)
        elif command == 'download':
            if len(args) < 2:
                print("Expected: project file ",file=sys.stderr)
                sys.exit(2)

            project = args[0]
            filepath = args[1]
            if len(args) == 3:
                targetfile = args[2]
            else:
                targetfile = os.path.basename(filepath)
            client.download(project, filepath, targetfile)
        else:
            print("Unknown command: " + command,file=sys.stderr)
            sys.exit(1)


        if data:
            if command == 'xml':
                print(data.xml)
            if command in ['info','get']:
                print("General Information")
                print("\tSystem ID:   " + data.system_id)
                print("\tSystem Name: " + data.system_name)
                print("\tSystem URL:  " + data.baseurl)
                if username:
                    print("\tUser:        " + username)
                if command == 'get':
                    print("\tProject:     " + data.project)
            if command in ['info','projects','index']:
                print("Projects")
                for project in data.projects:
                    print("\t" + project)
            if command in ['get','status']:
                print("Status Information")
                print("\tStatus: " + str(data.status)) #TODO: nicer messages
                print("\tStatus Message: " + data.statusmessage)
                print("\tCompletion: " + str(data.completion) + "%")
            if command in ['info','profiles']:
                print("Profiles:") #TODO: Implement
                for i, profile in enumerate(data.profiles):
                    print("\tProfile " + str(i+1))
                    print("\t Input")
                    for template in profile.input:
                        print("\t\t" + template.id + " - " + template.label)
                    print("\t Output")
                    for template in profile.output:
                        if isinstance(template, ParameterCondition):
                            for t in template.allpossibilities():
                                print("\t\t(CONDITIONAL!) " + t.id + " - " + t.label)
                        else:
                            print("\t\t" + template.id + " - " + template.label)
            if command == 'inputtemplates':
                print("Input templates:")
                for template in data.input:
                    print("\t\t" + template.id + " - " + template.label)
            if command == 'inputtemplate':
                try:
                    inputtemplate = data.inputtemplate(args[0])
                except:
                    print("No such inputtemplate",file=sys.stderr)
                    sys.exit(1)
                print("Inputtemplate parameters:")
                for parameter in inputtemplate.parameters:
                    print("\t\t" + str(parameter)) #VERIFY: unicode support?
                print("Inputtemplate converters:")
                for c in inputtemplate.converters:
                    print("\t\t" + c.id + " - " + c.label )
            if command in ['info','parameters']:
                print("Global Parameters:")
                for group, parameters in data.parameters:
                    print("\t" + group)
                    for parameter in parameters:
                        print("\t\t" + str(parameter))#VERIFY: unicode support?
            if command in ['get','input'] and data.input:
                print("Input files:")
                for f in data.input:
                    print("\t" + f.filename + "\t" + str(f),end="")
                    if f.metadata and f.metadata.inputtemplate:
                        print("\t" + f.metadata.inputtemplate)
                    else:
                        print
            if command in ['get','output'] and data.output:
                print("Output files:")
                for f in data.output:
                    print("\t" + f.filename + "\t" + str(f),end="")
                    if f.metadata and f.metadata.provenance and f.metadata.provenance.outputtemplate_id:
                        print("\t" + f.metadata.provenance.outputtemplate_id)
                    else:
                        print

    except NotFound:
        print("Not Found (404)",file=sys.stderr)
    except PermissionDenied:
        print("Permission Denied (403)",file=sys.stderr)
    except ServerError:
        print("Server Error! (500)",file=sys.stderr)
    except AuthRequired:
        print("Authorization required (401)",file=sys.stderr)


if __name__ == "__main__":
    main()
