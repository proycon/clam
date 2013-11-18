#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- WSGI script for launching CLAM (from within a webserver) --
#       by Maarten van Gompel (proycon)
#       http://proycon.github.io/clam
#
#       Copy and adapt this script for your particular service!
#
#       Licensed under GPLv3
#
###############################################################


import sys
import os

#** If CLAM is not by default in your PYTHONPATH, you need specify the directory that contains the subdirectory 'clam' here (and uncomment all lines): **
#CLAMPARENTDIR = '/path/to/clam'
#sys.path.append(CLAMPARENTDIR)
#os.environ['PYTHONPATH'] = CLAMPARENTDIR

WEBSERVICEDIR = '/path/to/yourwebservice/' #this is the directory that contains your service configuration file
sys.path.append(WEBSERVICEDIR)
os.environ['PYTHONPATH'] = WEBSERVICEDIR # + ':' + CLAMPARENTDIR

import yourwebservice #** import your configuration module here! **
import clam.clamservice
application = clam.clamservice.run_wsgi(yourwebservice) #** pass your module to CLAM **

