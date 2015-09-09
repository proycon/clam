#!/usr/bin/env python3
#-*- coding:utf-8 -*-

#** NOTE: Make sure the shebang (first line in this file) refers to the Python interpreter you
#want to use, which may be either Python 3 or 2 **

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- WSGI script for launching CLAM (from within a webserver) --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#
#       Copy and adapt this script for your particular service!
#
#       Licensed under GPLv3
#
###############################################################

import sys
import os
import site

#** This is the directory that contains your service configuration file, adapt it: **
WEBSERVICEDIR = '/path/to/yourwebservice/'

sys.path.append(WEBSERVICEDIR)
os.environ['PYTHONPATH'] = WEBSERVICEDIR

VIRTUALENV=None

#** If you installed CLAM locally in a virtual environment, uncomment and set the following **
#VIRTUALENV = "/path/to/virtualenv"

if VIRTUALENV:
    site.addsitedir(VIRTUALENV + '/lib/python'+str(sys.version_info.major) + '.' + str(sys.version_info.minor) + '/site-packages')
    activate_env = VIRTUALENV + '/bin/activate_this.py'
    exec(compile(open(activate_env).read(), activate_env, 'exec'))

import yourwebservice #** import your configuration module here! **
import clam.clamservice
application = clam.clamservice.run_wsgi(yourwebservice) #** pass your module to CLAM **

