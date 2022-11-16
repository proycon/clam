#! /usr/bin/env python
# -*- coding: utf8 -*-


import os
import io
from setuptools import setup


def getreadme():
    for fname in ('README.rst','README.md', 'README'):
        if os.path.exists(fname):
            return io.open(os.path.join(os.path.dirname(__file__), fname),'r',encoding='utf-8').read()
    return ""

setup(
    name = "SYSTEM_ID",
    version = "0.1", #make sure SYSTEM_VERSION in your service configuration is set to the same value!
    author = "Unspecified", #adapt this
    description = ("A CLAM webservice"), #adapt this with a better (short) description!
    license = "GPL-3.0-or-later",
    keywords = "clam webservice rest nlp computational_linguistics rest",
    url = "https://somewhere.over.the.rainbow", #update this!
    packages=['SYSTEM_ID'],
    long_description=getreadme(),
    classifiers=[
        "Development Status :: 5 - Production/Stable", #you may want to downgrade this
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Text Processing :: Linguistic", #check and remove or change if not relevant
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    package_data = {'SYSTEM_ID':['*.wsgi','*.yml','*.sh'] },
    include_package_data=True,
    install_requires=['CLAM >= 3.2']
)
