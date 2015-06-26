#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os
import site

VIRTUALENV=None

#** If you installed CLAM locally in a virtual environment, uncomment and set the following **
#VIRTUALENV = "/path/to/virtualenv"

if VIRTUALENV:
    site.addsitedir(VIRTUALENV + '/lib/python'+str(sys.version_info.major) + '.' + str(sys.version_info.minor) + '/site-packages')
    activate_env = VIRTUALENV + '/bin/activate_this.py'
    exec(compile(open(activate_env).read(), activate_env, 'exec'))

import clam.config.frog #** import your configuration module here! **
import clam.clamservice
application = clam.clamservice.run_wsgi(clam.config.frog) #** pass your module to CLAM **

