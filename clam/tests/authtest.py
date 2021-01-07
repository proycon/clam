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
import time
import random
import unittest
import io

#We may need to do some path magic in order to find the clam.* imports

sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

#Import the CLAM Client API and CLAM Data API and other dependencies
from clam.common.client import *
from clam.common.data import * #pylint: disable=redefined-builtin
from clam.common.formats import *
import clam.common.status

class AuthServiceTest(unittest.TestCase):
    """Test basic operations with authentication"""

    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url,'proycon','wrongpw')

    def test1_index(self):
        """No Access Test - Testing inability to access index with wrong user credentials"""
        self.assertRaises( AuthRequired, self.client.index)

    def test2_create(self):
        """No Access Test - Testing inability to create project with wrong user credentials"""
        self.assertRaises( AuthRequired, self.client.create, 'basicservicetest')

    def test3_project(self):
        """No Access Test - No project state retrieval with wrong user credentials"""
        self.assertRaises( AuthRequired, self.client.get, 'basicservicetest')

    def test4_index(self):
        """Access Test - Testing ability to access porch despite wrong user credentials"""
        data = self.client.porch()
        self.assertTrue(data.system_id == "authtest")
        self.assertTrue(data.profiles)
        self.assertTrue(data.parameters)
        self.assertFalse(data.projects)

class NoAuthServiceTest(unittest.TestCase):
    """Test basic operations without authentication"""

    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url)

    def test1_porch(self):
        """Access Test - Testing ability to access the porch (explicitly) without providing user credentials"""
        data = self.client.porch()
        self.assertTrue(data.system_id == "authtest")
        self.assertTrue(data.profiles)
        self.assertTrue(data.parameters)
        self.assertFalse(data.projects)

    def test2_porch(self):
        """Access Test - Testing ability to access the porch (implicitly) without providing user credentials"""
        data = self.client.getroot()
        self.assertTrue(data.system_id == "authtest")
        self.assertTrue(data.profiles)
        self.assertTrue(data.parameters)
        self.assertFalse(data.projects)

    def test3_index(self):
        """No Access Test - Testing inability to access the index"""
        self.assertRaises( AuthRequired, self.client.index)


class BasicServiceTest(unittest.TestCase):
    """Test basic operations with authentication"""

    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url,'proycon','secret')

    def test1_index(self):
        """Basic Service Test - Index and sanity"""
        data = self.client.index()
        self.assertTrue(data.system_id == "authtest")
        self.assertTrue(isinstance(data.projects,list))
        self.assertTrue(data.profiles)
        self.assertTrue(data.parameters)

    def test1_2_porch(self):
        """Basic Service Test - Porch and sanity"""
        data = self.client.porch()
        self.assertTrue(data.system_id == "authtest")
        self.assertTrue(data.profiles)
        self.assertTrue(data.parameters)
        self.assertFalse(data.projects)

    def test2_1_create(self):
        """Basic Service Test - Project creation"""
        success = self.client.create('basicservicetest')
        self.assertTrue(success)

    def test2_2_project(self):
        """Basic Service Test - Project availability in index"""
        data = self.client.index()
        self.assertTrue('basicservicetest' in data.projects)

    def test2_3_project(self):
        """Basic Service Test - Project state retrieval"""
        data = self.client.get('basicservicetest')
        self.assertTrue(data.system_id == "authtest")
        self.assertTrue(data.profiles)
        self.assertTrue(data.parameters)
        self.assertTrue(isinstance(data.input,list))

    def test2_3b_combo(self):
        """Basic Service Test - Simple combined run"""
        projectname = 'basicservicetest' + str(random.getrandbits(64))
        success = self.client.create(projectname)
        self.assertTrue(success)

        data = self.client.get(projectname)
        self.assertTrue(data.system_id == "authtest")
        self.assertTrue(data.profiles)
        self.assertTrue(data.parameters)
        self.assertTrue(isinstance(data.input,list))

        success = self.client.delete(projectname)
        self.assertTrue(success)


    def test2_4_upload(self):
        """Basic Service Test - File upload with extension"""
        f = io.open('/tmp/servicetest.txt','w',encoding='utf-8')
        f.write("On espère que tout ça marche bien.")
        f.close()
        data = self.client.get('basicservicetest')
        success = self.client.addinputfile('basicservicetest', data.inputtemplate('textinput'),'/tmp/servicetest.txt', language='fr')
        self.assertTrue(success)

    def test2_4b_upload(self):
        """Basic Service Test - Passing contents explicitly"""
        data = self.client.get('basicservicetest')
        success = self.client.addinput('basicservicetest', data.inputtemplate('textinput'),"On espère que tout ça marche bien.",filename='servicetest.txt', language='fr')
        self.assertTrue(success)

    def test2_5_upload(self):
        """Basic Service Test - File upload verification"""
        data = self.client.get('basicservicetest')
        found = False
        for f in data.input:
            if f.filename == 'servicetest.txt':
                found = True
        self.assertTrue(found)

    def test2_6_deletion(self):
        """Basic Service Test - File Deletion"""
        data = self.client.get('basicservicetest')
        success = False
        for f in data.input:
            if f.filename == 'servicetest.txt':
                success = f.delete()
        self.assertTrue(success)


    def test2_7_upload(self):
        """Basic Service Test - File upload without extension"""
        f = io.open('/tmp/servicetest','w',encoding='utf-8')
        f.write(u"On espère que tout ça marche bien.")
        f.close()
        data = self.client.get('basicservicetest')
        success = self.client.addinputfile('basicservicetest', data.inputtemplate('textinput'),'/tmp/servicetest', language='fr')
        self.assertTrue(success)


    def test2_8_upload(self):
        """Basic Service Test - File upload verification + metadata check"""
        data = self.client.get('basicservicetest')
        found = False
        for f in data.input:
            if f.filename == 'servicetest.txt':
                f.loadmetadata()
                self.assertTrue(f.metadata)
                found = True
        self.assertTrue(found)

    def test2_9_deletion(self):
        """Basic Service Test - File Deletion"""
        data = self.client.get('basicservicetest')
        success = False
        for f in data.input:
            if f.filename == 'servicetest.txt':
                success = f.delete()
        self.assertTrue(success)

    def test2_A_metadataerror(self):
        """Basic Service Test - Upload with parameter errors"""
        data = self.client.get('basicservicetest')
        try:
            success = self.client.addinputfile('basicservicetest', data.inputtemplate('textinput'),'/tmp/servicetest', language='nonexistant')
            self.assertFalse(success)
        except ParameterError:
            self.assertTrue(True) #pylint: disable=redundant-unittest-assert

    def test2_B_metadata(self):
        """Basic Service Test - Upload with explicit metadata file"""
        f = io.open('/tmp/servicetest.txt','w',encoding='utf-8')
        f.write("On espère que tout ça marche bien.")
        f.close()
        f = io.open('/tmp/servicetest.txt.METADATA','w',encoding='utf-8')
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<CLAMMetaData format="PlainTextFormat" mimetype="text/plain" inputtemplate="textinput">
<meta id="encoding">utf-8</meta>
<meta id="author">proycon</meta>
<meta id="language">fr</meta>
<meta id="year">2010</meta>
</CLAMMetaData>""")
        f.close()
        data = self.client.get('basicservicetest')
        success = self.client.addinputfile('basicservicetest', data.inputtemplate('textinput'),'/tmp/servicetest.txt', language='fr', metafile='/tmp/servicetest.txt.METADATA')
        self.assertTrue(success)

    def test2_C_delete(self):
        """Basic Service Test - Project deletion"""
        success = self.client.delete('basicservicetest')
        self.assertTrue(success)

class ExtensiveServiceTest(unittest.TestCase):
    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url,'proycon','secret')
        self.project = 'extservicetest'
        self.client.create(self.project)
        f = io.open('/tmp/servicetest.txt','w',encoding='utf-8')
        f.write(u"On espère que tout ça marche bien.")
        f.close()


    def test1_simplerun(self):
        """Extensive Service Test - Full simple run"""
        data = self.client.get(self.project)
        success = self.client.addinputfile(self.project, data.inputtemplate('textinput'),'/tmp/servicetest.txt', language='fr')
        self.assertTrue(success)
        data = self.client.start(self.project)
        self.assertTrue(data)
        self.assertFalse(data.errors)
        while data.status != clam.common.status.DONE:
            time.sleep(1) #wait 1 second before polling status
            data = self.client.get(self.project) #get status again
        self.assertFalse(data.errors, "Checking for absence of errors (" + data.errormsg + ")")
        self.assertTrue(isinstance(data.output, list))
        self.assertTrue('servicetest.txt.freqlist' in [ x.filename for x in data.output ])
        self.assertTrue('servicetest.txt.stats' in [ x.filename for x in data.output ])
        for outputfile in data.output:
            if outputfile.filename == 'servicetest.txt.freqlist':
                outputfile.loadmetadata()
                #print outputfile.metadata.provenance.outputtemplate_id
                self.assertTrue(outputfile.metadata.provenance.outputtemplate_id == 'freqlistbydoc')
            if outputfile.filename == 'servicetest.txt.stats':
                outputfile.loadmetadata()
                #print outputfile.metadata.provenance.outputtemplate_id
                self.assertTrue(outputfile.metadata.provenance.outputtemplate_id == 'statsbydoc')

    def test2_parametererror(self):
        """Extensive Service Test - Global parameter error"""
        data = self.client.get(self.project)
        success = self.client.addinputfile(self.project, data.inputtemplate('textinput'),'/tmp/servicetest.txt', language='fr')
        self.assertTrue(success)
        try:
            data = self.client.start(self.project, casesensitive='nonexistant')
            self.assertTrue(data)
        except ParameterError:
            self.assertTrue(True) #pylint: disable=redundant-unittest-assert


    def test3_conditionaloutput(self):
        """Extensive Service Test - Output conditional on parameter"""
        data = self.client.get(self.project)
        success = self.client.addinputfile(self.project, data.inputtemplate('textinput'),'/tmp/servicetest.txt', language='fr')
        self.assertTrue(success)
        data = self.client.start(self.project, createlexicon=True)
        self.assertTrue(data)
        self.assertFalse(data.errors)
        while data.status != clam.common.status.DONE:
            time.sleep(1) #wait 1 second before polling status
            data = self.client.get(self.project) #get status again
        self.assertFalse(data.errors)
        self.assertTrue(isinstance(data.output, list))
        self.assertTrue('servicetest.txt.freqlist' in [ x.filename for x in data.output ])
        self.assertTrue('servicetest.txt.stats' in [ x.filename for x in data.output ])
        self.assertTrue('overall.lexicon' in [ x.filename for x in data.output ])
        for outputfile in data.output:
            if outputfile.filename == 'servicetest.txt.freqlist':
                outputfile.loadmetadata()
                self.assertTrue(outputfile.metadata.provenance.outputtemplate_id == 'freqlistbydoc')
            if outputfile.filename == 'servicetest.txt.stats':
                outputfile.loadmetadata()
                self.assertTrue(outputfile.metadata.provenance.outputtemplate_id == 'statsbydoc')
            if outputfile.filename == 'overall.lexicon':
                outputfile.loadmetadata()
                self.assertTrue(outputfile.metadata.provenance.outputtemplate_id == 'lexicon')

    def test4_storetest(self):
        """Extensive Service Test - Storage test"""
        data = self.client.get(self.project)
        success = self.client.addinputfile(self.project, data.inputtemplate('textinput'),'/tmp/servicetest.txt', language='fr')
        self.assertTrue(success)
        data = self.client.start(self.project)
        self.assertTrue(data)
        self.assertFalse(data.errors)
        while data.status != clam.common.status.DONE:
            time.sleep(1) #wait 1 second before polling status
            data = self.client.get(self.project) #get status again
        self.assertFalse(data.errors, "Checking for absence of errors (" + data.errormsg + ")")
        self.assertTrue(isinstance(data.output, list))
        self.assertTrue('servicetest.txt.freqlist' in [ x.filename for x in data.output ])
        self.assertTrue('servicetest.txt.stats' in [ x.filename for x in data.output ])
        for outputfile in data.output:
            if outputfile.filename == 'servicetest.txt.freqlist':
                outputfile.loadmetadata()
                #print outputfile.metadata.provenance.outputtemplate_id
                response = outputfile.store()
                self.assertTrue('id' in response)
                print("Stored file ID " + response['id'],file=sys.stderr)
                self.assertTrue('url' in response)
                filename = self.client.downloadstorage(response['id'],targetdir="/tmp") #unauthenticated by default
                self.assertTrue(os.path.exists(filename))


    def tearDown(self):
        self.client.delete(self.project)




class ArchiveUploadTest(unittest.TestCase):
    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url,'proycon','secret')
        self.project = 'archivetest'
        self.client.create(self.project)
        f = io.open('/tmp/servicetest.txt','w',encoding='utf-8')
        f.write(u"On espère que tout ça marche bien.")
        f.close()
        f = io.open('/tmp/servicetest2.txt','w',encoding='utf-8')
        f.write(u"Non, rien de rien, non je ne regrette rien.")
        f.close()
        f = io.open('/tmp/servicetest3.txt','w',encoding='utf-8')
        f.write(u"Ni le mal qu'on m'a fait, ni le bien, tout ça me semble égal!")
        f.close()
        os.system('zip /tmp/servicetest.zip /tmp/servicetest.txt /tmp/servicetest2.txt /tmp/servicetest3.txt')
        os.system('tar -cvzf /tmp/servicetest.tar.gz /tmp/servicetest.txt /tmp/servicetest2.txt /tmp/servicetest3.txt')

    def test1_zip(self):
        """Archive Upload Test - ZIP file"""
        data = self.client.get(self.project)
        success = self.client.addinputfile(self.project, data.inputtemplate('textinput'),'/tmp/servicetest.zip', language='fr')
        self.assertTrue(success)
        data = self.client.get(self.project) #get status again
        self.assertTrue('servicetest.txt' in [ x.filename for x in data.input ])
        self.assertTrue('servicetest2.txt' in [ x.filename for x in data.input ])
        self.assertTrue('servicetest3.txt' in [ x.filename for x in data.input ])

    def test2_targz(self):
        """Archive Upload Test - TAR.GZ file"""
        data = self.client.get(self.project)
        success = self.client.addinputfile(self.project, data.inputtemplate('textinput'),'/tmp/servicetest.tar.gz', language='fr')
        self.assertTrue(success)
        data = self.client.get(self.project) #get status again
        self.assertTrue('servicetest.txt' in [ x.filename for x in data.input ])
        self.assertTrue('servicetest2.txt' in [ x.filename for x in data.input ])
        self.assertTrue('servicetest3.txt' in [ x.filename for x in data.input ])

    def tearDown(self):
        self.client.delete(self.project)

if __name__ == '__main__':
    unittest.main(verbosity=2)
