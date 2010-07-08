#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- WSGI script for launching CLAM (from within a webserver) --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Copy and adapt this script for your particular service!
#
#       Licensed under GPLv3
#
###############################################################



#** If CLAM is not by default in your PYTHONPATH, you need specify the directory that contains the subdirectory 'clam' here (and uncomment all five lines): **

#import os
#import sys
#CLAMDIR = '/home/proycon/work'
#sys.path.append(CLAMDIR)
#os.environ['PYTHONPATH'] = CLAMDIR

import clam.config.yourapp #** import your configuration module here! **
import clam.clamservice
application = clam.clamservice.run_wsgi(clam.config.yourapp) #** pass your module to CLAM **

