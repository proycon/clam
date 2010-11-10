###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Format classes --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

from clam.common.metadata import CLAMMetaData


class PlainText(CLAMMetaData):
    attributes = {'encoding':True,'language':False } #attributes with True are always required!
    mimetype = "text/plain"

    def __init__(self, **kwargs):
        super(PlainTextFormat,self).__init__(**kwargs)
            
                
class TadpoleFormat(CLAMMetaData):    
    attributes = {'encoding':True,'language':False } #attributes with True are always required!
    
    name = "Tadpole Output Format"
    mimetype = 'text/plain'

    def __init__(self, **kwargs ):
        super(TadpoleFormat,self).__init__(**kwargs)


class DCOIFormat(CLAMMetaData):    
    
    name = "DCOI format"
    mimetype = 'text/xml'

    def __init__(self, **kwargs):
        super(DCOIFormat,self).__init__(**kwargs)


class KBXMLFormat(CLAMMetaDatas):
    
    name = "Koninklijke Bibliotheek XML-formaat"
    mimetype = 'text/xml'

    def __init__(self, **kwargs ):
        super(KBXMLFormat,self).__init__(encoding, extensions, **kwargs)

