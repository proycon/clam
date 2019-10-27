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
import unittest
import io
import zipfile

#We may need to do some path magic in order to find the clam.* imports

sys.path.append(sys.path[0] + '/../../')
os.environ['PYTHONPATH'] = sys.path[0] + '/../../'

#Import the CLAM Client API and CLAM Data API and other dependencies
from clam.common.client import *
from clam.common.data import * #pylint: disable=redefined-builtin
from clam.common.formats import *
import clam.common.status


class ConstraintServiceTest(unittest.TestCase):
    def setUp(self):
        self.url = 'http://' + os.uname()[1] + ':8080'
        self.client = CLAMClient(self.url)
        self.project = 'constrainttest'
        self.client.create(self.project)
        f = io.open('/tmp/pos.folia.xml','w',encoding='utf-8')
        f.write("""<?xml version="1.0" encoding="utf-8"?>
<FoLiA xmlns="http://ilk.uvt.nl/folia" version="2.0" xml:id="example">
  <metadata>
      <annotations>
          <text-annotation />
          <token-annotation set="https://raw.githubusercontent.com/LanguageMachines/uctodata/master/setdefinitions/tokconfig-eng.foliaset.ttl">
			 <annotator processor="p1" />
		  </token-annotation>
          <sentence-annotation>
			 <annotator processor="p1" />
          </sentence-annotation>
          <paragraph-annotation>
			 <annotator processor="p1" />
          </paragraph-annotation>
          <pos-annotation set="brown"> <!-- This is an ad-hoc set declaration as it is no URL and therefore not really defined -->
			 <annotator processor="p1" />
          </pos-annotation>
      </annotations>
      <provenance>
         <processor xml:id="p1" name="proycon" type="manual" />
      </provenance>
  </metadata>
  <text xml:id="example.text">
    <s xml:id="example.p.1.s.2">
     <w xml:id="example.p.1.s.2.w.1" class="WORD">
        <t>This</t>
        <pos class="DT"/>
     </w>
     <w xml:id="example.p.1.s.2.w.2" class="WORD">
        <t>is</t>
        <pos class="VBZ"/>
     </w>
     <w xml:id="example.p.1.s.2.w.3" class="WORD">
        <t>an</t>
        <pos class="AT"/>
     </w>
     <w xml:id="example.p.1.s.2.w.4" class="WORD" space="no">
        <t>example</t>
        <pos class="NN"/>
     </w>
     <w xml:id="example.p.1.s.2.w.5" class="PUNCTUATION">
        <t>.</t>
        <pos class="."/>
     </w>
    </s>
  </text>
</FoLiA>
""")
        f.close()
        f = io.open('/tmp/nopos.folia.xml','w',encoding='utf-8')
        f.write("""<?xml version="1.0" encoding="utf-8"?>
<FoLiA xmlns="http://ilk.uvt.nl/folia" version="2.0" xml:id="example">
  <metadata>
      <annotations>
          <text-annotation />
          <token-annotation set="https://raw.githubusercontent.com/LanguageMachines/uctodata/master/setdefinitions/tokconfig-eng.foliaset.ttl">
			 <annotator processor="p1" />
		  </token-annotation>
          <sentence-annotation>
			 <annotator processor="p1" />
          </sentence-annotation>
          <paragraph-annotation>
			 <annotator processor="p1" />
          </paragraph-annotation>
      </annotations>
      <provenance>
         <processor xml:id="p1" name="proycon" type="manual" />
      </provenance>
  </metadata>
  <text xml:id="example.text">
    <s xml:id="example.p.1.s.2">
     <w xml:id="example.p.1.s.2.w.1" class="WORD">
        <t>This</t>
     </w>
     <w xml:id="example.p.1.s.2.w.2" class="WORD">
        <t>is</t>
     </w>
     <w xml:id="example.p.1.s.2.w.3" class="WORD">
        <t>an</t>
     </w>
     <w xml:id="example.p.1.s.2.w.4" class="WORD" space="no">
        <t>example</t>
     </w>
     <w xml:id="example.p.1.s.2.w.5" class="PUNCTUATION">
        <t>.</t>
     </w>
    </s>
  </text>
</FoLiA>
""")
        f.close()

    def tearDown(self):
        self.client.delete(self.project)

    def test1_validconstraint(self):
        """Constraint Service Test - Constraint passes"""
        data = self.client.get(self.project)
        success = self.client.addinputfile(self.project, data.inputtemplate('foliainput'),'/tmp/pos.folia.xml')
        self.assertTrue(success)
        data = self.client.start(self.project)
        self.assertTrue(data)
        self.assertFalse(data.errors)
        while data.status != clam.common.status.DONE:
            time.sleep(1) #wait 1 second before polling status
            data = self.client.get(self.project) #get status again
        self.assertFalse(data.errors)
        self.assertTrue(isinstance(data.output, list))
        self.assertTrue('posfreqlist.tsv' in [ x.filename for x in data.output ])
        for outputfile in data.output:
            if outputfile.filename == 'posfreqlist.tsv':
                outputfile.loadmetadata()
                #print outputfile.metadata.provenance.outputtemplate_id
                self.assertTrue(outputfile.metadata.provenance.outputtemplate_id == 'posfreqlist')

    def test2_invalidconstraint(self):
        """Constraint Service Test - Constraint fails"""
        data = self.client.get(self.project)
        try:
            success = self.client.addinputfile(self.project, data.inputtemplate('foliainput'),'/tmp/nopos.folia.xml')
            self.assertTrue(False, "Exception should have been raised on file upload")
        except Exception as e:
            self.assertTrue(True, "Testing whether exception is raised on file upload")

if __name__ == '__main__':
    unittest.main(verbosity=2)
