#! /usr/bin/env python
# -*- coding: utf8 -*-

import os
import sys
from setuptools import setup

os.chdir(os.path.dirname(sys.argv[0]))
if not os.path.exists('clam'):   
    print >>sys.stderr, "Preparing build"
    if not os.path.exists('build'): os.mkdir('build')   
    os.chdir('build')
    if not os.path.exists('clam'): os.mkdir('clam')
    os.system('cp -Rpdf ../* clam/ 2> /dev/null')
    os.system('mv -f clam/setup.py .')
    os.system('cp -f clam/README .')  

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "CLAM",
    version = "0.7.8.1",
    author = "Maarten van Gompel",
    author_email = "proycon@anaproy.nl",
    description = ("Computational Linguistics Application Mediator. Turn command-line NLP tools into fully fledged RESTful webservices."),
    license = "GPL",
    keywords = "clam webservice rest nlp computational_linguistics rest",
    url = "http://ilk.uvt.nl/clam",
    packages=['clam','clam.common','clam.config','clam.external','clam.external.poster','clam.wrappers'],
    long_description=read('../README'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 2.6",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points = {
        'console_scripts': [
            'clamservice = clam.startclamservice:main',
            'startclamservice = clam.startclamservice:main', #alias 
        ]
    },
    package_data = {'clam':['static/*.*','static/custom/*','static/tableimages/*','templates/*','style/*'] },
    install_requires=['web.py >= 0.33','lxml >= 2.2']
)
