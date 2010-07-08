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

class AbstractViewer(object):

    id = __name__ #you may insert another meaningful ID here, no spaces or special chars!
    name = "Unspecified Viewer" 

    def __init__(self, **kwargs):
        self.embed = False #Embed external sites as opposed to redirecting?
        for key, value in kwargs.items():
            if key == 'embed':
                value = bool(value)
                self.embed = value

    def url(self, file):
        """Returns the URL to view this resource, the link may be an external service/website. If necessary, the file can be 'pushed' to the service from here. file is a CLAMOutputFile instance"""
        return False

    def view(self, file, **kwargs):
        """Returns the view itself, in xhtml (it's recommended to use web.py's template system!). file is a CLAMOutputFile instance. This always issues a GET to the remote service."""
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


