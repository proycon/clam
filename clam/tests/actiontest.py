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

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import time
import glob
import random
import unittest
import io

#We may need to do some path magic in order to find the clam.* imports

sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

#Import the CLAM Client API and CLAM Data API and other dependencies
from clam.common.client import *
from clam.common.data import *
from clam.common.formats import *
import clam.common.status


class ActionServiceTest(unittest.TestCase):
    """Test basic operations"""

    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url)

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

if __name__ == '__main__':
    unittest.main(verbosity=2)
