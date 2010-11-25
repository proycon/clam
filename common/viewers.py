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


import web
import urllib2
from urllib import urlencode

from lxml import etree

class AbstractViewer(object):

    id = 'abstractviewer' #you may insert another meaningful ID here, no spaces or special chars!
    name = "Unspecified Viewer" 

    def __init__(self, **kwargs):
        self.embed = False #Embed external sites as opposed to redirecting?
        for key, value in kwargs.items():
            if key == 'embed':
                value = bool(value)
                self.embed = value

    def url(self, file):
        """Returns the URL to view this resource, the link is usually an external service/website. If necessary, the file can be 'pushed' to the service from here. file is a CLAMOutputFile instance"""
        return False

    def view(self, file, **kwargs):
        """Returns the view itself, in xhtml (it's recommended to use web.py's template system!). file is a CLAMOutputFile instance. By default, if not overriden and a remote service is specified, this issues a GET to the remote service."""
        url = self.url(file) + urlencode(kwargs)
        if url: #is the resource external?
            if self.embedded:
                #fetch
                req = urllib2.urlopen(url)
                for line in req.readlines():
                    yield line
            else:
                #redirect
                raise web.seeother(url)

    def generator(self):
        if isgenerator




class FrogViewer(AbstractViewer):
    id = 'frogviewer'
    name = "Frog Viewer"

    def view(self,file,**kwargs):
        render = web.template.render('templates')
        return render.crudetableviewer( file, "\t")



class SoNaRViewer(AbstractViewer):
    id = 'sonarviewer'
    name = "SoNaR Viewer"

    def view(self, file, **kwargs):
        xslfile = "static/sonar.xsl"
        xslt_doc = etree.parse(xslfile)
        transform = etree.XSLT(xslt_doc)

        f = file.open()
        xml_doc = etree.parse(f.readlines())

        return str(transform(xml_doc))



