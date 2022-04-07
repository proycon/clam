#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Data tests --
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
import json

#We may need to do some path magic in order to find the clam.* imports
sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

import clam.common.data
import clam.common.parameters
import clam.common.formats
import clam.common.converters

class InputTemplateTest(unittest.TestCase):
    def generate(self):
        return clam.common.data.InputTemplate('test', clam.common.formats.PlainTextFormat,"test",
            clam.common.parameters.StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),
            clam.common.parameters.ChoiceParameter(id='language',name='Language',description='The language the text is in', choices=[('en','English'),('nl','Dutch'),('fr','French')]),
            clam.common.converters.CharEncodingConverter(id='latin1',label='Convert from Latin-1',charset='iso-8859-1'),
            clam.common.converters.PDFtoTextConverter(id='pdfconv',label='Convert from PDF Document'),
            clam.common.converters.MSWordConverter(id='docconv',label='Convert from MS Word Document'),
            extension='.txt',
            multi=True
        )

    def setUp(self):
        self.data = self.generate()


    def test1_equality(self):
        """Input template - Shallow equality check (ID only)"""
        self.assertTrue(self.data == self.generate())


    def test2_sanity(self):
        """Input template - Sanity check (deeper equality)"""
        self.assertTrue(self.data.label == 'test')
        self.assertTrue(self.data.formatclass == clam.common.formats.PlainTextFormat)
        self.assertTrue(isinstance(self.data.parameters[0], clam.common.parameters.StaticParameter))
        self.assertTrue(self.data.parameters[0].id == 'encoding')
        self.assertTrue(isinstance(self.data.parameters[1], clam.common.parameters.ChoiceParameter))
        self.assertTrue(self.data.parameters[1].id == 'language')
        self.assertTrue(self.data.converters[0].id == 'latin1')
        self.assertTrue(self.data.converters[1].id == 'pdfconv')
        self.assertTrue(self.data.converters[2].id == 'docconv')
        self.assertTrue(self.data.extension == 'txt')
        self.assertFalse(self.data.unique)

    def test3_equality(self):
        """Input template - Deep equality check after XML generation and parsing"""
        xml = self.data.xml()
        data = clam.common.data.InputTemplate.fromxml(xml)
        self.assertTrue(data.formatclass == clam.common.formats.PlainTextFormat)
        self.assertTrue(isinstance(data.parameters[0], clam.common.parameters.StaticParameter))
        self.assertTrue(data.parameters[0].id == 'encoding')
        self.assertTrue(isinstance(data.parameters[1], clam.common.parameters.ChoiceParameter))
        self.assertTrue(data.parameters[1].id == 'language')
        self.assertTrue(data.extension == 'txt')
        self.assertFalse(data.unique)
        #NOTE: converters not supported client-side


class OutputTemplateTest(unittest.TestCase):
    def generate(self):
        return clam.common.data.OutputTemplate('test', clam.common.formats.PlainTextFormat,'test',
            clam.common.data.SetMetaField('x1','y1'),
            clam.common.data.UnsetMetaField('x2','y2'),
            clam.common.data.ParameterMetaField('z','z'),
            clam.common.data.CopyMetaField('a','a.a'),
            clam.common.data.ParameterCondition(author_set=True,
                then=clam.common.data.ParameterMetaField('author','author'),
            ),
            filename='test',
            unique=True
        )

    def setUp(self):
        self.data = self.generate()


    def test1_equality(self):
        """Output template - Shallow equality check (ID only)"""
        self.assertTrue(self.data == self.generate())


    def test2_sanity(self):
        """Output template - Sanity check (Deeper equality)"""
        self.assertTrue(self.data.formatclass == clam.common.formats.PlainTextFormat)
        self.assertTrue(self.data.label == 'test')
        self.assertTrue(isinstance(self.data.metafields[0], clam.common.data.SetMetaField))
        self.assertTrue(isinstance(self.data.metafields[1], clam.common.data.UnsetMetaField))
        self.assertTrue(isinstance(self.data.metafields[2], clam.common.data.ParameterMetaField))
        self.assertTrue(isinstance(self.data.metafields[3], clam.common.data.CopyMetaField))
        self.assertTrue(self.data.filename == 'test')
        self.assertTrue(self.data.unique)

    def test3_equality(self):
        """Output template - Deep equality check after XML generation and parsing"""
        xml = self.data.xml()
        data = clam.common.data.OutputTemplate.fromxml(xml)
        self.assertTrue(data.formatclass == clam.common.formats.PlainTextFormat)
        self.assertTrue(isinstance(data.metafields[0], clam.common.data.SetMetaField))
        self.assertTrue(isinstance(data.metafields[1], clam.common.data.UnsetMetaField))
        self.assertTrue(isinstance(data.metafields[2], clam.common.data.ParameterMetaField))
        self.assertTrue(isinstance(data.metafields[3], clam.common.data.CopyMetaField))
        #self.assertTrue(data.filename == 'test')  #always gives error, client unaware of server filename
        self.assertTrue(data.unique)
        #note: viewers and converters not supported client-side

class ParameterCondition(unittest.TestCase):
    def generate(self):
        return clam.common.data.ParameterCondition(x=True,
            then=clam.common.data.SetMetaField('x','yes'),
            otherwise=clam.common.data.SetMetaField('x','no'),
        )

    def setUp(self):
        self.data = self.generate()

    def test1_sanity(self):
        """Parameter Condition - Sanity check"""
        self.assertTrue(len(self.data.conditions) == 1)
        self.assertTrue(isinstance(self.data.then, clam.common.data.SetMetaField))
        self.assertTrue(isinstance(self.data.otherwise, clam.common.data.SetMetaField))


    def test2_equality(self):
        """Parameter Condition - Equality check after XML generation and parsing"""
        xml = self.data.xml()
        data = clam.common.data.ParameterCondition.fromxml(xml)
        self.assertTrue(len(data.conditions) == 1)
        self.assertTrue(isinstance(data.then, clam.common.data.SetMetaField))
        self.assertTrue(isinstance(data.otherwise, clam.common.data.SetMetaField))

    def test3_evaluation(self):
        """Parameter Condition - Evaluation Check (BooleanParameter True, with otherwise)"""
        parameters = { 'x': clam.common.parameters.BooleanParameter('x', 'x','x',value=True) }
        out = self.data.evaluate(parameters)
        self.assertTrue(isinstance(out, clam.common.data.SetMetaField))
        self.assertTrue(out.key == 'x')
        self.assertTrue(out.value == 'yes')

    def test32_evaluation(self):
        """Parameter Condition - Evaluation Check (BooleanParameter True, without otherwise)"""
        self.data = clam.common.data.ParameterCondition(x=True,
            then=clam.common.data.SetMetaField('x','yes'),
        )
        parameters = { 'x': clam.common.parameters.BooleanParameter('x', 'x','x',value=True) }
        out = self.data.evaluate(parameters)
        self.assertTrue(isinstance(out, clam.common.data.SetMetaField))
        self.assertTrue(out.key == 'x')
        self.assertTrue(out.value == 'yes')


    def test4_evaluation(self):
        """Parameter Condition - Evaluation Check (BooleanParameter False (explicit), with otherwise)"""
        parameters = { 'x': clam.common.parameters.BooleanParameter('x', 'x','x',value=False) }
        out = self.data.evaluate(parameters)
        self.assertTrue(isinstance(out, clam.common.data.SetMetaField))
        self.assertTrue(out.key == 'x')
        self.assertTrue(out.value == 'no')

    def test5_evaluation(self):
        """Parameter Condition - Evaluation Check (BooleanParameter False (implicit), with otherwise)"""
        parameters = {}
        out = self.data.evaluate(parameters)
        self.assertTrue(isinstance(out, clam.common.data.SetMetaField))
        self.assertTrue(out.key == 'x')
        self.assertTrue(out.value == 'no')

    def test6_evaluation(self):
        """Parameter Condition - Evaluation Check (BooleanParameter False (implicit), without otherwise)"""
        self.data = clam.common.data.ParameterCondition(x=True,
            then=clam.common.data.SetMetaField('x','yes'),
        )
        parameters = {}
        out = self.data.evaluate(parameters)
        self.assertTrue(out == False)

class ParametersInFilename(unittest.TestCase):
    def setUp(self):
        self.inputtemplate = clam.common.data.InputTemplate('test', clam.common.formats.PlainTextFormat,"test",
            clam.common.parameters.StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),
            clam.common.parameters.ChoiceParameter(id='language',name='Language',description='The language the text is in', choices=[('en','English'),('nl','Dutch'),('fr','French')]),
            filename='test.$encoding.$language.txt',
            unique=True
        )

    def test1_inputfilename(self):
        """Input Template - Testing resolution of filename with parameters"""
        postdata = {'language':'fr','encoding':'utf-8'}
        validmeta, metadata, parameters = self.inputtemplate.generate(None, None, postdata)
        self.assertTrue(validmeta)
        self.assertTrue(isinstance(metadata,clam.common.data.CLAMMetaData))
        filename = clam.common.data.resolveinputfilename(self.inputtemplate.filename, parameters, self.inputtemplate, 0)
        self.assertEqual(filename,'test.utf-8.fr.txt')



    def test2_outputfilename(self):
        """Output Template - Testing resolution of filename with parameters"""
        postdata = {'language':'fr','encoding':'utf-8'}
        validmeta, metadata, parameters = self.inputtemplate.generate(None, None, postdata)
        self.assertTrue(validmeta)
        self.assertTrue(isinstance(metadata,clam.common.data.CLAMMetaData))
        filename = clam.common.data.resolveinputfilename(self.inputtemplate.filename, parameters, self.inputtemplate, 0)
        self.assertEqual(filename,'test.utf-8.fr.txt')


class ExternalConfigTest(unittest.TestCase):

    def test1_substenvvars(self):
        """External YAML Config - Substitute variable from environment"""
        os.environ['SIMPLETESTVAR'] = "/test"
        s_in = '{{SIMPLETESTVAR}}/frog_webservice-userdata'
        s_ref = '/test/frog_webservice-userdata'
        s_out = clam.common.data.resolveconfigvariables(s_in, {})
        self.assertEqual(s_out,s_ref)

    def test2_substenvvars(self):
        """External YAML Config - Substitute variable from environment (2)"""
        os.environ['CLAM_TEST_ROOT1'] = "/test"
        s_in = '{{CLAM_TEST_ROOT1}}/frog_webservice-userdata'
        s_ref = '/test/frog_webservice-userdata'
        s_out = clam.common.data.resolveconfigvariables(s_in, {})
        self.assertEqual(s_out,s_ref)

    def test3_emptyenvvars(self):
        """External YAML Config - Non-existing variable (allow to pass)"""
        s_in = '{{CLAM_TEST_ROOT2}}/frog_webservice-userdata'
        s_ref = '/frog_webservice-userdata'
        s_out = clam.common.data.resolveconfigvariables(s_in, {})
        self.assertEqual(s_out,s_ref)

    def test4_resolveenvvars(self):
        """External YAML Config - Non-existing variable, fall back to specified default"""
        s_in = '{{CLAM_TEST_ROOT2=/tmp}}/frog_webservice-userdata'
        s_ref = '/tmp/frog_webservice-userdata'
        s_out = clam.common.data.resolveconfigvariables(s_in, {})
        self.assertEqual(s_out,s_ref)

    def test5_emptyenvvars_fail(self):
        """External YAML Config - Non-existing variable (hard failure)"""
        s_in = '{{CLAM_TEST_ROOT2!}}'
        self.assertRaises(clam.common.data.ConfigurationError, clam.common.data.resolveconfigvariables, s_in, {})


    def test6_substenvvars_typecast(self):
        """External YAML Config - Type casting (int)"""
        os.environ['SIMPLETESTVAR'] = "42"
        s_in = '{{SIMPLETESTVAR|int}}'
        s_ref = 42
        s_out = clam.common.data.resolveconfigvariables(s_in, {})
        self.assertEqual(s_out,s_ref)

    def test7_substenvvars_typecast_bool(self):
        """External YAML Config - Type casting (bool)"""
        os.environ['SIMPLETESTVAR'] = "true"
        s_in = '{{SIMPLETESTVAR|bool=false}}'
        s_ref = True
        s_out = clam.common.data.resolveconfigvariables(s_in, {})
        self.assertEqual(s_out,s_ref)

    def test8_substenvvars_typecast_json(self):
        """External YAML Config - Type casting (json)"""
        s_ref = { "a": 1, "b": 2 }
        os.environ['COMPLEXVAR'] = json.dumps(s_ref)
        s_in = '{{COMPLEXVAR|json}}'
        s_out = clam.common.data.resolveconfigvariables(s_in, {})
        self.assertEqual(s_out,s_ref)

    def test9_substenvvars_typecast_json(self):
        """External YAML Config - Type casting (json)"""
        s_in = '{{DOESNOTEXIST|json}}'
        s_out = clam.common.data.resolveconfigvariables(s_in, {})
        self.assertEqual(s_out,None)


if __name__ == '__main__':
    unittest.main()
