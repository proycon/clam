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


#pylint: disable=wrong-import-position, unused-wildcard-import

import sys
import os
import unittest

#We may need to do some path magic in order to find the clam.* imports

sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

#Import the CLAM Client API and CLAM Data API and other dependencies
from clam.common.client import *
from clam.common.data import * #pylint: disable=redefined-builtin
from clam.common.formats import *


class NoAuthActionServiceTest(unittest.TestCase):
    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url)

    def test1_action(self):
        """Action Test (Function with viewer), with allowanonymous"""
        result = self.client.action('tabler',text="a,b,c", viewer="simpletableviewer")
        self.assertTrue(result.startswith("<!DOCTYPE"))


class AuthActionServiceTest(unittest.TestCase):
    """Test authenticated actions"""

    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url,'proycon','secret',basicauth=True)

    def test1_action(self):
        """Action Test (Command)"""
        result = self.client.action('uppercase',text="test")
        self.assertEqual(result.strip(), "TEST")

    def test2_action(self):
        """Action Test (Command) - Unicode"""
        result = self.client.action('uppercase',text="téstя")
        self.assertEqual(result.strip(), "TéSTя") #tr doesn't do unicode well

    def test3_action(self):
        """Action Test (Function)"""
        result = self.client.action('multiply',x=2,y=3)
        self.assertEqual(result.strip(), "6")

    def test4_action(self):
        """Action Test (Function with viewer)"""
        result = self.client.action('tabler',text="a,b,c", viewer="simpletableviewer")
        self.assertTrue(result.startswith("<!DOCTYPE"))

    def test5_action(self):
        """Action Test (Command return username)"""
        result = self.client.action('returnuser')
        self.assertEqual(result.strip(), "proycon")

if __name__ == '__main__':
    unittest.main(verbosity=2)
