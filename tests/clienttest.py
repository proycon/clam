#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os

sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

from clam.common.client import *

clamclient = CLAMClient('http://localhost:8080/')


#index of all projects
print "PROJECT INDEX"
index = clamclient.index()
for project in index.projects:
    print "\t" + project        

#creating new project
clamclient.create('clienttest')

#get new project
data = clamclient.get('clienttest')







