#! /usr/bin/env python
# -*- coding: utf8 -*-

import sys
import os

statusfile = sys.argv[1]
inputdir = sys.argv[2]
outputdir = sys.argv[3]
parameters = ' '.join(sys.argv[4:])

import glob

for inputfile in glob.glob(inputdir + '/*.train'):
    trainfile = inputfile
    

for testfile in glob.glob(inputdir + '/*.test'):
    outfile = os.path.basename(testfile).split('.')[0] + '.timblout'    
    os.system('timbl ' + parameters + ' -t ' + testfile + ' -o ' + outfile)
    
if parameters.find('-t leave_one_out') != -1:
    os.system('timbl ' + parameters + ' -o ' + outfile)  

    
    
    
