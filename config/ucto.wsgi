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
#       Licensed under GPLv3
#
###############################################################

import os
import sys


sys.path.append('/var/www')
os.environ['PYTHONPATH'] = '/var/www'
os.environ['LD_LIBRARY_PATH'] = '/var/www/lib:/usr/local/lib:/usr/lib:/lib'

import clam.config.ucto
import clam.clamservice
application = clam.clamservice.run_wsgi(clam.config.ucto)


