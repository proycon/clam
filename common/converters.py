###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Converters --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under the GNU Public License v3
#
###############################################################

from clam.common.data import CLAMMetaData
import clam.common.formats

class AbstractConverter(object):
    acceptfrom = [] #List of formats; conversion is accepted from these into the target format(Override this!)
    acceptto = [] #List of formats; conversion is accepted from the target format into these (Override this!)
    
    label = "(ERROR: label not overriden from AbstractConverter!)" #Override this with a sensible name
    
    def __init__(self, **kwargs):        
        if 'label' in kwargs:
            self.label = kwargs['label']
            
    def convertfrom(self,fromfilepath, tofilepath, metadata):        
        """Convert from target format into one of the source formats. Relevant if converters are used in InputTemplates. Metadata already is metadata for the to-be-generated file."""        
        assert isinstance(metadata, CLAMMetaData) #metadata of the destination file (file to be generated here)        
        if not metadata.__class__ in self.:
            raise Exception("Convertor " + self.__class__.__name__ + " can not convert input files to " + metadata.__class__.__name__ + "!")
        return False  #conversion unsuccessful (cause this is an abstract method, needs to be overriden)
        
    def convertto(self,sourcefile, targetfilepath):
        """Convert from one of the source formats into target format. Relevant if converters are used in OutputTemplates. Sourcefile is a CLAMOutputFile instance."""    
                assert isinstance(metadata, CLAMMetaData) #metadata of the destination file (file to be generated here)        
        if not metadata.__class__ in self.acceptfrom:
            raise Exception("Convertor " + self.__class__.__name__ + " can not convert input files to " + metadata.__class__.__name__ + "!")
        return False #conversion unsuccessful (cause this is an abstract method, needs to be overriden)
        
        
class CharEncodingConverter(AbstractConverter):
    acceptfrom = acceptto = [clam.common.formats.PlainTextFormat]
    
    label = "CharEncodingConverter" #to be overriden in instance creation
    
    def __init__(self, **kwargs):
        if not 'label' in kwargs:
            raise Exception("No label specified for EncodingConvertor!")
        
        if 'fromcharset' in kwargs:
            self.fromcharset = kwargs['from']
        else:
            raise Exception("EncodingConvertor expects fromcharset= !")
            
        if 'tocharset' in kwargs:
            self.tocharset = kwargs['to']
        else:
            raise Exception("EncodingConvertor expects fromcharset= !")

        super(EncodingConvertor,self).__init__(**kwargs)
      
    def convertfrom(self,fromfilepath, tofilepath, metadata=None):
        """Convert from target format into one of the source formats. Relevant if converters are used in InputTemplates. Metadata already is metadata for the to-be-generated file."""
        super(EncodingConvertor,self).__init_( **kwargs)
        #TODO: Implement
        raise NotImplementedError
        
        
    def convertto(self,sourcefile, targetfilepath):
        """Convert from one of the source formats into target format. Relevant if converters are used in OutputTemplates. Sourcefile is a CLAMOutputFile instance."""    
        super(EncodingConvertor,self).__init_( **kwargs)
        #TODO: Implement
        raise NotImplementedError
        

