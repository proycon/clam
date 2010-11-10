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

class ExampleFormat(CLAMMetaData):

    #A dictionary of attributes that this format can take, the keys correspond
    #to the attributes, the values can be either:
    # True   - Accept any value, this attribute is required
    # False  - Accept any value, but this attribute is not required
    # a list - Accept any of the specified values (if False is a member then this attribute is not required)
    # a specific value - Simply always assign this static value
    attributes = {'encoding':True, 'language':False, 'colour': ['green','red','blue'], 'pi':3.14 }
    
    #Do you want to allow any other custom attributes? Defined by the InputTemplate/OutputTemplate
    allowcustomattributes = True
    
    #Specify a mimetype for your format
    mimetype = "text/plain"
    
    #If your format is XML-based, specify a scheme:
    #scheme = None
    

class PlainText(CLAMMetaData):
    attributes = {'encoding':True,'language':False }
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

