#! /usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import print_function

import os
import io
from setuptools import setup


def read(fname):
    return io.open(os.path.join(os.path.dirname(__file__), fname),'r',encoding='utf-8').read()

setup(
    name = "CLAM",
    version = "2.4.6", #also change in clam.common.data.VERSION and dispatcher.py and codemeta.json
    author = "Maarten van Gompel",
    author_email = "proycon@anaproy.nl",
    description = ("Turns command-line NLP tools into fully-fledged RESTful webservices with an auto-generated web-interface for human end-users."),
    license = "GPL",
    keywords = "clam webservice rest nlp computational_linguistics rest",
    url = "https://proycon.github.io/clam",
    packages=['clam','clam.common','clam.config','clam.wrappers'],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3", #3.0, 3.1 and 3.2 are not supported by flask
        "Programming Language :: Python :: 3.4", #3.0, 3.1 and 3.2 are not supported by flask
        "Programming Language :: Python :: 3.5", #3.0, 3.1 and 3.2 are not supported by flask
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points = {
        'console_scripts': [
            'clamservice = clam.clamservice:main',
            'startclamservice = clam.clamservice:main', #alias
            'clamnewproject = clam.clamnewproject:main', #alias
            'clamdispatcher = clam.clamdispatcher:main',
            'clamclient = clam.clamclient:main'
        ]
    },
    package_data = {'clam':['static/*.*','static/custom/*','static/tableimages/*','templates/*','style/*','clients/*.py','tests/*.py','tests/*.yml','wrappers/*.sh','config/*.wsgi'] },
    include_package_data=True,
    install_requires=['flask >= 0.10','lxml >= 2.2','requests','requests_oauthlib','requests_toolbelt','pycrypto','certifi', 'pyyaml']
)
