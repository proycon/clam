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

import unittest
import sys
import os

#We may need to do some path magic in order to find the clam.* imports
sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

import clam.common.data
import clam.common.parameters


class BooleanParameterTest(unittest.TestCase):
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



class IntegerParameterTest(unittest.TestCase):
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
        """Integer parameter - setting to value out of range (lower)"""
        success = self.parameter.set(0)
        self.assertTrue(self.parameter.error == "Number must be a whole number between 1 and 10")
        self.assertFalse(success)
        self.assertFalse(self.parameter.hasvalue)


    def test41_set_outofrange(self):
        """Integer parameter - setting to value out of range (higher)"""
        success = self.parameter.set(11)
        self.assertTrue(self.parameter.error == "Number must be a whole number between 1 and 10")
        self.assertFalse(success)
        self.assertFalse(self.parameter.hasvalue)


    def test5_set_float(self):
        """Integer parameter - setting to float (automatically converted)"""
        success = self.parameter.set(5.6)
        self.assertTrue(success)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == 6)

    def test6_set_string(self):
        """Integer parameter - setting to text (invalid)"""
        success = self.parameter.set('test')
        #print self.parameter.error
        self.assertTrue(self.parameter.error == "Not a number", self.parameter.error)
        self.assertFalse(success)
        self.assertFalse(self.parameter.hasvalue)


class FloatParameterTest(unittest.TestCase):
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

class StringParameterTest(unittest.TestCase):
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


    def test32_set_value(self):
        """String parameter - setting to a valid value that contains spaces"""
        success = self.parameter.set("t t t")
        self.assertTrue(self.parameter.error is None, self.parameter.error)
        self.assertTrue(self.parameter.hasvalue)
        self.assertTrue(self.parameter.value == "t t t")
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

class ChoiceParameterTest(unittest.TestCase):
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

class MultiChoiceParameterTest(unittest.TestCase):
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

    def test5_fromxml(self):
        """MultiChoice parameter - reading from XML"""
        xml = """<ChoiceParameter id="skip" name="Skip modules" description="Are there any components you want to skip? Skipping components you do not need may speed up the process considerably." flag="--skip=" multi="true"> <choice id="t">Tokeniser</choice> <choice id="m" selected="1">Multi-Word Detector</choice> <choice id="p" selected="1">Parser</choice> <choice id="c" selected="1">Chunker / Shallow parser</choice> <choice id="n" selected="1">Named Entity Recognition</choice></ChoiceParameter>"""
        parameter = clam.common.parameters.AbstractParameter.fromxml(xml)
        self.assertTrue(isinstance(parameter, clam.common.parameters.ChoiceParameter))
        self.assertTrue(parameter.multi == True)
        self.assertTrue(len(parameter.choices) == 5)
        self.assertTrue(isinstance(parameter.value, list))
        self.assertTrue(not 't' in parameter.value)
        self.assertTrue('p' in parameter.value)
        self.assertTrue('m' in parameter.value)
        self.assertTrue('c' in parameter.value)
        self.assertTrue('n' in parameter.value)


class ParameterProcessingTest(unittest.TestCase):
    """Parameter Processing Tests"""

    def setUp(self):
        #string REQUIRES boolean (but not vice versa)
        #float FORBIDS int (and vice versa)
        #choice is required
        self.nogroups = [
            clam.common.parameters.StringParameter('teststring','test','test',paramflag='-s',maxlength=10, require=['testbool']),
            clam.common.parameters.ChoiceParameter('testchoice','test','test',choices=[('a','A'),('b','B'),('c','C')], paramflag='-c',required=True),
            clam.common.parameters.FloatParameter('testfloat','test','test',paramflag='-f',min=0.0,max=1.0, forbid=['testint']),
            clam.common.parameters.IntegerParameter('testint','test','test',paramflag='-i',min=1,max=10,forbid=['testfloat']),
            clam.common.parameters.BooleanParameter('testbool','test','test',paramflag='-b')
        ]
        self.groups = [
            ('Main',
                self.nogroups
            )
        ]
        #valid settings
        self.postdata = {'teststring': 'test', 'testbool': True, 'testint': 4, 'testchoice':'c'}

    def test1_sanity_nogroup(self):
        """Parameter Processing - Sanity check (no group)"""
        errors, parameters, _ = clam.common.data.processparameters(self.postdata, self.nogroups)
        self.assertFalse(errors)
        self.assertTrue(parameters[0].id == 'teststring')
        self.assertTrue(parameters[1].id == 'testchoice')
        self.assertTrue(parameters[2].id == 'testfloat')
        self.assertTrue(parameters[3].id == 'testint')
        self.assertTrue(parameters[4].id == 'testbool')

    def test2_sanity_group(self):
        """Parameter Processing - Sanity check (group)"""
        errors, parameters, _ = clam.common.data.processparameters(self.postdata, self.groups)
        self.assertFalse(errors)
        group, parameters = parameters[0]
        self.assertTrue(group == 'Main')
        self.assertTrue(parameters[0].id == 'teststring')
        self.assertTrue(parameters[1].id == 'testchoice')
        self.assertTrue(parameters[2].id == 'testfloat')
        self.assertTrue(parameters[3].id == 'testint')
        self.assertTrue(parameters[4].id == 'testbool')

    def test3_valuecheck_nogroup(self):
        """Parameter Processing - Value check (no group)"""
        errors, parameters, _ = clam.common.data.processparameters(self.postdata, self.nogroups)
        self.assertFalse(errors)
        self.assertTrue(parameters[0].value == self.postdata['teststring'])
        self.assertTrue(parameters[1].value == self.postdata['testchoice'])
        self.assertFalse(parameters[2].hasvalue)
        self.assertTrue(parameters[3].value == self.postdata['testint'])
        self.assertTrue(parameters[4].value == self.postdata['testbool'])

    def test4_valuecheck_group(self):
        """Parameter Processing - Value check (group)"""
        errors, parameters, _ = clam.common.data.processparameters(self.postdata, self.groups)
        self.assertFalse(errors)
        group, parameters = parameters[0]
        self.assertTrue(parameters[0].value == self.postdata['teststring'])
        self.assertTrue(parameters[1].value == self.postdata['testchoice'])
        self.assertFalse(parameters[2].hasvalue)
        self.assertTrue(parameters[3].value == self.postdata['testint'])
        self.assertTrue(parameters[4].value == self.postdata['testbool'])

    def test5_commandline(self):
        """Parameter Processing - Command line argument check"""
        errors, parameters, commandlineargs = clam.common.data.processparameters(self.postdata, self.groups)
        self.assertFalse(errors)
        self.assertTrue(commandlineargs == ['-s test', '-c c', '-i 4', '-b']) #order same as defined

    def test6_required(self):
        """Parameter Processing - Forgetting a required parameter (independent)"""
        postdata = {'teststring': 'test', 'testbool': True, 'testint': 4}
        errors, parameters, commandlineargs = clam.common.data.processparameters(postdata, self.nogroups)
        self.assertTrue(errors)
        self.assertTrue(parameters[1].id == 'testchoice')
        self.assertTrue(parameters[1].error)

    def test7_require(self):
        """Parameter Processing - Forgetting a required parameter (dependent)"""
        postdata = {'teststring': 'test',  'testint': 4,'testchoice':'c'}
        errors, parameters, commandlineargs = clam.common.data.processparameters(postdata, self.nogroups)
        self.assertTrue(errors)
        self.assertTrue(parameters[0].id == 'teststring')
        self.assertTrue(parameters[0].error)

    def test8_forbid(self):
        """Parameter Processing - Setting a forbidden parameter combination (dependent)"""
        postdata = {'teststring': 'test',  'testint': 4,'testfloat':0.5, 'testchoice':'c', 'testbool':False}
        errors, parameters, commandlineargs = clam.common.data.processparameters(postdata, self.nogroups)
        self.assertTrue(errors)
        self.assertTrue(parameters[2].id == 'testfloat')
        self.assertTrue(parameters[2].error)
        self.assertTrue(parameters[3].id == 'testint')
        self.assertTrue(parameters[3].error)




if __name__ == '__main__':
    unittest.main(verbosity=2)

