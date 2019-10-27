
import sys
import os
import time

sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

from clam.common.client import *
from clam.common.formats import *
import clam.common.status

clamclient = CLAMClient('http://localhost:8080/')


#index of all projects
print("INDEX OF ALL PROJECTS")
index = clamclient.index()
for project in index.projects:
    print("\t" + project)


#this is the name of our test project
project = "clienttest"


#check if project already exists
if project in index.projects:
    clamclient.delete(project) #delete it ruthlessly

#get new project
clamclient.create(project)

#get project state
data = clamclient.get(project)
if data.status == clam.common.status.READY: #should always be the case, since we just created it
    #make a testfile
    f = open('/tmp/tst','w')
    f.write("Dit is een test.")
    f.close()

    #upload it (of course we could better use a StringIO here)
    print("Uploading file...")
    clamclient.upload(project, open('/tmp/tst'), PlainTextFormat('utf-8') )

    #print the parameters we have
    print("PARAMETERS:")
    for parametergroup, parameters in data.parameters:
        for parameter in parameters:
            print("\t" + parameter.name + ": " + str(parameter.value))

    #set some parameters (by their ID)
    #note that using this method, exceptions will be raised automatically when the parameter values do not validate!
    data['boolean'] = True
    data['integer'] = 5
    data['float'] = 0.5
    data['text'] = "This is a very short text."
    data['colourchoice'] = 'green'
    data['cities'] = ['london','paris','amsterdam']


    data = clamclient.start(project, **data.passparameters())
    if data.errors:
        print("An error occured: " + data.errormsg,file=sys.stderr)
        sys.exit(1)


    while data.status != clam.common.status.DONE:
        time.sleep(5) #wait 5 seconds
        data = clamclient.get(project) #get status again
        print("STATUS: " + str(data.completion) + '% -- ' + data.statusmessage)



    #yay, we're done!
    #List all output files:
    print("OUTPUT FILES:")
    for outputfile in data.output:
        print("\tFILE: " + str(outputfile) + " (" + outputfile.format.name + ")")
        print("\tCONTENTS: ")
        #Download and immediately read the output file
        for line in outputfile:
            print("\t\t" + line.encode('utf-8'),end='')
        print()






