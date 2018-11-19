###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Viewers --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       Licensed under GPLv3
#
###############################################################

from __future__ import print_function, unicode_literals, division, absolute_import

#pylint: disable=wrong-import-order

import csv
import sys
import os.path
import random
import requests
from lxml import etree
if sys.version < '3':
    from StringIO import StringIO #pylint: disable=import-error
else:
    from io import StringIO,  BytesIO

try:
    import foliatools
except ImportError:
    foliatools = None
try:
    import flask
except ImportError:
    pass

from clam.common.util import withheaders

class AbstractViewer(object):

    id = 'abstractviewer' #you may insert another meaningful ID here, no spaces or special chars!
    name = "Unspecified Viewer"
    mimetype = 'text/html'

    def __init__(self, **kwargs):
        self.embed = False #Embed external sites as opposed to redirecting?
        for key, value in kwargs.items():
            if key == 'embed':
                value = bool(value)
                self.embed = value


    def view(self, file, **kwargs):
        """Returns the view itself, in xhtml (it's recommended to use flask's template system!). file is a CLAMOutputFile instance. By default, if not overriden and a remote service is specified, this issues a GET to the remote service."""
        raise NotImplementedError

class ForwardViewer(AbstractViewer):
    """The ForwardViewer calls a remote service and passes a backlink where the remote service can download an output file. The remote service is in turn expected to return a HTTP Redirect (302) response. It is implemented as a :class:`Forwarder`. See :ref:`forwarders`"""

    def __init__(self, id, name, forwarder, **kwargs):
        self.id = id
        self.name = name
        self.forwarder = forwarder
        super(ForwardViewer,self).__init__(**kwargs)

    def view(self, file, **kwargs):
        self.forwarder(None, file)
        r = requests.get(self.forwarder.forwardlink, allow_redirects=True)
        if r.status_code == 302 and 'Location' in r.headers:
            url = r.headers['Location']
            return flask.redirect(url)
        else:
            return "Unexpected response from Forward service (HTTP " + str(r.status_code) + ", target was " + url + "): " + r.text




class SimpleTableViewer(AbstractViewer):
    id = 'tableviewer'
    name = "Table viewer"

    def __init__(self, **kwargs):
        if 'quotechar' in kwargs:
            self.quotechar = kwargs['quotechar']
            del kwargs['quotechar']
        else:
            self.quotechar = ''

        if 'delimiter' in kwargs:
            self.delimiter = kwargs['delimiter']
            del kwargs['delimiter']
        else:
            self.delimiter = '\t'

        if 'wordwrap' in kwargs:
            self.wordwrap = kwargs['wordwrap']
        else:
            self.wordwrap = True

        if 'customcss' in kwargs:
            self.customcss = kwargs['customcss']
        else:
            self.customcss = ""


        super(SimpleTableViewer,self).__init__(**kwargs)

    def read(self, file):
        file = csv.reader(file, delimiter=self.delimiter)
        for line in file:
            yield line

    def view(self,file,**kwargs):
        return flask.render_template('crudetableviewer.html',file=file,tableviewer=self, wordwrap=self.wordwrap, customcss=self.customcss)


class XSLTViewer(AbstractViewer):
    id = 'xsltviewer'
    name = "XML Viewer"

    def __init__(self, **kwargs):
        if 'file' in kwargs:
            self.xslfile = kwargs['file']
            del kwargs['file']
        else:
            raise Exception("XSLTViewer expect file= parameter with XSL file")

        super(XSLTViewer,self).__init__(**kwargs)

    def view(self, file, **kwargs):
        xslt_doc = etree.parse(self.xslfile)
        transform = etree.XSLT(xslt_doc)

        lines = file.readlines()
        if lines:
            if sys.version < '3' and isinstance(lines[0], unicode): #pylint: disable=undefined-variable
                xml_doc = etree.parse(StringIO("".join( ( x.encode('utf-8') for x in lines) ) ))
            else:
                if sys.version > '3' and isinstance(lines[0],str):
                    xml_doc = etree.parse(BytesIO("".join( ( x.encode('utf-8') for x in lines) ) ))
                elif sys.version < '3' and isinstance(lines[0], str):
                    xml_doc = etree.parse(StringIO(b"".join(lines) ))
                else:
                    xml_doc = etree.parse(BytesIO(b"".join(lines) ))
        else:
            return "(no data)"

        return str(transform(xml_doc))

class FoLiAViewer(AbstractViewer):
    id = 'foliaviewer'
    name = "FoLiA Viewer"

    def view(self, file, **kwargs):
        if foliatools is None:
            raise Exception("FoliA-Tools are not installed,  these are required for FoLiA visualisation! pip install FoLiA-tools")
        xslfile = foliatools.__path__[0] + "/folia2html.xsl"
        xslt_doc = etree.parse(xslfile)
        transform = etree.XSLT(xslt_doc)

        lines = file.readlines()
        if lines:
            if sys.version < '3' and isinstance(lines[0], unicode): #pylint: disable=undefined-variable
                xml_doc = etree.parse(StringIO("".join( ( x.encode('utf-8') for x in lines) ) ))
            else:
                if sys.version > '3' and isinstance(lines[0],str):
                    xml_doc = etree.parse(BytesIO(b"".join( ( x.encode('utf-8') for x in lines) ) ))
                elif sys.version < '3' and isinstance(lines[0], str):
                    xml_doc = etree.parse(StringIO(b"".join(lines) ))
                else:
                    xml_doc = etree.parse(BytesIO(b"".join(lines) ))
        else:
            return "(no data)"

        return str(transform(xml_doc))


class SoNaRViewer(AbstractViewer):
    id = 'sonarviewer'
    name = "SoNaR Viewer"

    def view(self, file, **kwargs):
        xslfile = os.path.dirname(__file__) + "/../static/sonar.xsl"
        xslt_doc = etree.parse(xslfile)
        transform = etree.XSLT(xslt_doc)

        if sys.version < '3':
            xml_doc = etree.parse(StringIO("".join(file.readlines()).encode('utf-8')))
        else:
            xml_doc = etree.parse(BytesIO("".join(file.readlines()).encode('utf-8')))

        return str(transform(xml_doc))


class FLATViewer(AbstractViewer):
    id = 'flatviewer'
    name = "Open in FLAT"

    def __init__(self, **kwargs):
        if 'url' in kwargs:
            self.url = kwargs['url']
            del kwargs['url']
        else:
            self.url = ''

        if 'configuration' in kwargs:
            self.configuration = kwargs['configuration']
            del kwargs['configuration']
        else:
            self.configuration = ''

        if 'mode' in kwargs:
            self.mode = kwargs['mode']
            del kwargs['mode']
        else:
            self.mode = ''

        super(FLATViewer,self).__init__(**kwargs)

    def view(self, file, **kwargs):
        #filename will contain a random component to prevent clashes
        filename = os.path.basename(file.filename).replace('.folia.xml','').replace('.xml','') +  str("%034x" % random.getrandbits(128)) + '.folia.xml'
        r = requests.post(self.url + '/pub/upload/', allow_redirects=False, files=[('file',(filename,file,'application/xml'))], data={'configuration':self.configuration,'mode':self.mode})
        #FLAT redirects after upload, we catch the redirect rather than following it automatically, and return it ourselves as our redirect
        if r.status_code == 302 and 'Location' in r.headers:
            if r.headers['Location'][:4].lower() == 'http': #location is an absolute URL
                url = r.headers['Location']
            elif self.url and self.url[-1] == '/' and r.headers['Location'][0] == '/':
                url = self.url[:-1] + r.headers['Location']
            else:
                url = self.url + r.headers['Location']
            return flask.redirect(url)
        else:
            return "Unexpected response from FLAT (HTTP " + str(r.status_code) + ", target was " + self.url + "): " + r.text

