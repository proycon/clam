#!/usr/bin/env python3
# -*- coding: utf8 -*-

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os

statusfile = sys.argv[1]
inputdir = sys.argv[2]
outputdir = sys.argv[3]
parameters = ' '.join(sys.argv[4:])

import glob
from clam.common.data import shellsafe


trainfile = None
for inputfile in glob.glob(inputdir + '/*.train'):
    trainfile = inputfile

if not trainfile:
    print("No trainfile found",file=sys.stderr)

for testfile in glob.glob(inputdir + '/*.test'):
    outfile = outputdir + '/' + os.path.basename(testfile).split('.')[0] + '.timblout'
    cmd = 'timbl -f ' + shellsafe(trainfile,"'") + ' ' + parameters + ' -t ' + shellsafe(testfile,"'") + ' -o ' + shellsafe(outfile,"'")
    print("Processing " + testfile + ": " + cmd,file=sys.stderr)
    os.system(cmd)

if parameters.find('-t leave_one_out') != -1:
    print("Testing with leave-one-out",file=sys.stderr)
    os.system('timbl -f ' + shellsafe(trainfile,"'") + ' ' + parameters + ' -o ' + shellsafe(outfile,"'"))




