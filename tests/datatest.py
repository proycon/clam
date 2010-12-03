#!/usr/bin/env python
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

import unittest2
import sys
import os

#We may need to do some path magic in order to find the clam.* imports
sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

import clam.common.data
import clam.common.parameters
import clam.common.formats
import clam.common.converters

class InputTemplateTest(unittest2.TestCase):
    def geninputtemplate(self):
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
        self.data = self.geninputtemplate()  
    
    
    def test1_equality(self):
        """Input template - Shallow equality check (ID only)"""
        self.assertTrue(self.data == self.geninputtemplate())

        
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


class OutputTemplateTest(unittest2.TestCase):
    def genoutputtemplate(self):
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
        self.data = self.genoutputtemplate()  
    
    
    def test1_equality(self):
        """Output template - Shallow equality check (ID only)"""
        self.assertTrue(self.data == self.genoutputtemplate())

        
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
        
                                            
                                            
if __name__ == '__main__':
    unittest2.main(verbosity=2)
