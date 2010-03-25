#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Upload processor --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
# Processes and validates a file that has already been uploaded
#
###############################################################


import subprocess
import sys

#Dynamic import of service module
servicemodule = sys.argv[1]
if not servicemodule.isalpha():  #security precaution
    print >> sys.stderr, "ERROR: Invalid service module specified!"
else:
    import_string = "from " + sys.argv[1] + " import ROOT, INPUTFORMATS"
    exec import_string

project = sys.argv[1]
project = project.replace('..','') #security, no escaping the root
INPUTPATH = ROOT + 'projects/' + project + "/input/"

MAXDEPTH = 3

def isarchive(filename):
    return (filename[-3:] == '.gz' or filename[-4:] == '.bz2' or filename[-4:] == '.zip')

def extract(filename, format):
    if filename[-7:] == '.tar.gz':
    elif filename[-7:] == '.tar.bz2':
    elif filename[-3:] == '.gz':
    elif filename[-4:] == '.bz2':
    elif filename[-4:] == '.zip':
        

def validate(filename, format):
    global INPUTPATH
    if not format.validate(INPUTPATH + filename):
        print "<validated filename=\"" + filename+ "\" value=\"yes\" />"
    else:
        print "<validated filename=\"" + filename+ "\" value=\"no\" />"

def test(filename, format_id, depth = 0):
    global MAXDEPTH        
    inputformat = None
    for f in INPUTFORMATS:
        if f.__class__.name == format_id:
            inputformat = f
    prefix = (depth + 1) * "\t"
    print prefix + "<file name=\""+filename+"\"",
    if not os.path.exists(INPUTPATH + filename):
        print " uploaded=\"no\" />"
    else:
        if not inputformat:
            print " recognized=\"no\" />",
        elif isarchive(filename):
            print " archive=\"yes\">",
        elif inputformat:
            print " validated=\""+validate(filename, inputformat)+"\" />",
        
        if isarchive(filename):            
            for subfilename in extract(filename, inputformat):
                test(subfilename, format_id, depth + 1)
            print prefix + "</file>"    


it = iter(sys.argv[2:])
args = zip(it, it)

print "<clamupload>"
for filename, format_id in args:
    test(filename, format_id)
print "</clamupload>"            
    






