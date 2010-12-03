#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Parameter tests --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

import unittest2
import sys
import os

#We may need to do some path magic in order to find the clam.* imports
sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

import clam.common.parameters


class BooleanParameterTest(unittest2.TestCase):
    """Boolean Parameter Test"""
    
    def setUp(self):
        self.parameter = clam.common.parameters.BooleanParameter('test','test','test',paramflag='-t')
    
    def test1_sanity(self):
        """Boolean parameter - Sanity check"""
        self.assertTrue(self.parameter.id == self.parameter.name == self.parameter.description == 'test')
    
    def test2_set_true(self):
        """Boolean parameter - Setting to True"""
        success = self.parameter.set(True)
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(success and self.parameter.hasvalue and self.parameter.value is True)

    def test3_set_false(self):
        """Boolean parameter - Setting to False"""
        success = self.parameter.set(False)
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(success and self.parameter.hasvalue and self.parameter.value is False)
    
        
    def test4_compilearg(self):
        """Boolean parameter - Compiling for command line"""
        success = self.parameter.set(True)        
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(success)
        self.assertTrue(self.parameter.hasvalue)        
        self.assertTrue(self.parameter.value is True)
        param = self.parameter.compilearg()
        self.assertTrue(param == "-t")
        
        

class IntegerParameterTest(unittest2.TestCase):
    """Integer Parameter Test"""
    
    def setUp(self):
        self.parameter = clam.common.parameters.IntegerParameter('test','test','test',paramflag='-t',min=1,max=10)
    
    def test1_sanity(self):
        """Integer parameter - sanity check"""
        self.assertTrue(self.parameter.id == 'test')
        self.assertTrue(self.parameter.name == self.parameter.description == 'test')
    
    def test2_set_mininrange(self):
        """Integer parameter - Setting to minimum value in range"""
        success = self.parameter.set(1)
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == 1)
        self.assertTrue(success)        
    
        
        
    def test3_set_maxinrange(self):
        """Integer parameter - Setting to maximum value in range"""
        success = self.parameter.set(10)
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == 10 )
        self.assertTrue(success)
        
        
    def test4_set_outofrange(self):
        """Integer parameter - setting to value out of range"""
        success = self.parameter.set(0)
        self.assertTrue(self.parameter.error == "Number must be a whole number between 1 and 10")
        self.assertFalse(success)
        self.assertFalse(self.parameter.hasvalue)
        
        
class FloatParameterTest(unittest2.TestCase):
    """Float Parameter Test"""
    
    def setUp(self):
        self.parameter = clam.common.parameters.FloatParameter('test','test','test',paramflag='-t',min=0.0,max=1.0)
    
    def test1_sanity(self):
        """Float parameter - sanity check"""
        self.assertTrue(self.parameter.id == 'test')
        self.assertTrue(self.parameter.name == self.parameter.description == 'test')
    
    def test2_set_mininrange(self):
        """Float parameter - setting to to minimum value in range"""
        success = self.parameter.set(0)
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == 0)
        self.assertTrue(success)        

        
    def test3_set_midrange(self):
        """Float parameter - setting to middle value in range"""
        success = self.parameter.set(0.5)
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == 0.5 )
        self.assertTrue(success)
        
        
    def test4_set_maxinrange(self):
        """Float parameter - setting to maximum value in range"""
        success = self.parameter.set(1)
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == 1 )
        self.assertTrue(success)
        
        
    def test5_set_outofrange(self):
        """Float parameter - setting to value out of range"""
        success = self.parameter.set(2)
        self.assertTrue(self.parameter.error == "Number must be between 0.0 and 1.0")
        self.assertFalse(success)
        self.assertFalse(self.parameter.hasvalue)                        
                        
class StringParameterTest(unittest2.TestCase):
    """String Parameter Test"""
    
    def setUp(self):
        self.parameter = clam.common.parameters.StringParameter('test','test','test',paramflag='-t',maxlength=10)
    
    def test1_sanity(self):
        """String parameter - sanity check"""
        self.assertTrue(self.parameter.id == 'test')
        self.assertTrue(self.parameter.name == self.parameter.description == 'test')
    
    def test2_set_empty(self):
        """String parameter - setting to an empty value"""
        success = self.parameter.set("")
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == "")
        self.assertTrue(success)        
    

    def test3_set_value(self):
        """String parameter - setting to a valid value"""
        success = self.parameter.set("test")
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == "test")
        self.assertTrue(success)        
        
    def test4_set_maxsize(self):
        """String parameter - setting to value that is as long as it may get"""
        success = self.parameter.set("1234567890")
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == "1234567890")
        self.assertTrue(success)   
        
    def test5_set_toolong(self):
        """String parameter - Setting to value that is too long"""
        success = self.parameter.set("1234567890A")
        self.assertTrue(self.parameter.error == "Text too long, exceeding maximum of 10 characters allowed")
        self.assertFalse(success)
        self.assertFalse(self.parameter.hasvalue) 
        
class ChoiceParameterTest(unittest2.TestCase):
    """Choice Parameter Test"""
    
    def setUp(self):
        self.parameter = clam.common.parameters.ChoiceParameter('test','test','test',choices=[('a','A'),('b','B'),('c','C')],paramflag='-t' )
                        
    def test1_sanity(self):
        """Choice parameter - sanity check"""
        self.assertTrue(self.parameter.id == 'test')
        self.assertTrue(self.parameter.name == self.parameter.description == 'test')
        self.assertTrue(self.parameter.multi == False)                    
        self.assertTrue(len(self.parameter.choices) == 3)                    

    def test2_set_value(self):
        """Choice parameter - setting to a valid value"""
        success = self.parameter.set("a")
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == "a")
        self.assertTrue(success)
        
    def test3_set_invalid(self):
        """Choice parameter - setting to an invalid value"""
        success = self.parameter.set("d")
        self.assertTrue(self.parameter.error)
        self.assertFalse(success)
        self.assertFalse(self.parameter.hasvalue)

class MultiChoiceParameterTest(unittest2.TestCase):
    """Choice Parameter Test"""
    
    def setUp(self):
        self.parameter = clam.common.parameters.ChoiceParameter('test','test','test',choices=[('a','A'),('b','B'),('c','C')], paramflag='-t',multi=True )
                        
    def test1_sanity(self):
        """MultiChoice parameter - sanity check"""
        self.assertTrue(self.parameter.id == 'test')
        self.assertTrue(self.parameter.name == self.parameter.description == 'test')
        self.assertTrue(self.parameter.multi == True)                    
        self.assertTrue(len(self.parameter.choices) == 3)                    

    def test2_set_value(self):
        """MultiChoice parameter - setting to a single valid value"""
        success = self.parameter.set(["a"])
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == ["a"])
        self.assertTrue(success)
        
    def test3_set_valuemulti(self):
        """MultiChoice parameter - setting to multiple valid value"""
        success = self.parameter.set(['a','b','c'])
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == ['a','b','c'])
        self.assertTrue(success)
        
    def test4_set_invalid(self):
        """MultiChoice parameter - setting to an invalid value"""
        success = self.parameter.set("d")
        self.assertTrue(self.parameter.error)
        self.assertFalse(success)
        self.assertFalse(self.parameter.hasvalue)
                

                        
                                        
if __name__ == '__main__':
    unittest2.main(verbosity=2)
    
