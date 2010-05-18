#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os

sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

from clam.common.client import *
from clam.common.formats import *

clamclient = CLAMClient('http://localhost:8080/')


#index of all projects
print "INDEX OF ALL PROJECTS"
index = clamclient.index()
for project in index.projects:
    print "\t" + project        
    

#creating new project
clamclient.create('clienttest')

#get new project
data = clamclient.get('clienttest')

#make a testfile
f = open('/tmp/tst','w')
f.write("Dit is een test.")
f.close()

#upload it (of course we could better use a StringIO here)
clamclient.upload('clienttest', open('/tmp/tst'), 'tst', PlainTextFormat('utf-8') )












