#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Client for Text Statistics webservice --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

import sys
import os
import time
import glob
import random
import codecs
import unittest2

#We may need to do some path magic in order to find the clam.* imports

sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

#Import the CLAM Client API and CLAM Data API and other dependencies
from clam.common.client import *
from clam.common.data import *
from clam.common.formats import *
import clam.common.status


class BasicServiceTest(unittest2.TestCase):
    """Test basic operations"""
    
    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url)

    def test1_index(self):
        """Basic Service Test - Index and and sanity"""
        data = self.client.index()
        self.assertTrue(data.system_id == "textstats")
        self.assertTrue(isinstance(data.projects,list))
        self.assertTrue(data.profiles)
        self.assertTrue(data.parameters)

    def test2_1_create(self):
        """Basic Service Test - Project creation"""
        success = self.client.create('basicservicetest')
        self.assertTrue(success)
        
    def test2_2_create(self):
        """Basic Service Test - Project availability in index"""
        data = self.client.index()
        self.assertTrue('basicservicetest' in data.projects)
    
    def test2_3_create(self):
        """Basic Service Test - Project state retrieval"""
        data = self.client.get('basicservicetest')
        self.assertTrue(data.system_id == "textstats")
        self.assertTrue(data.profiles)
        self.assertTrue(data.parameters)        
        self.assertTrue(isinstance(data.input,list))        
        
    def test2_4_upload(self):
        """Basic Service Test - File upload"""
        f = codecs.open('/tmp/servicetest.txt','w','utf-8')
        f.write(u"On espère que tout ça marche bien.")
        f.close()
        success = clamclient.addinputfile('basicservicetest', data.inputtemplate('textinput'),'/tmp/servicetest.txt', language='fr')
        self.assertTrue(success)        

    def test2_5_delete(self):
        """Basic Service Test - Project deletion"""
        success = self.client.delete('basicservicetest')
        self.assertTrue(success)
        
class ExtensiveServiceTest(unittest2.TestCase):
    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url)    
    
        
