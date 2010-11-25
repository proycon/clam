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

import web
from clam.common.data import CLAMMetaData
import clam.common.formats

class AbstractConverter(object):
    acceptfrom = [] #List of formats; conversion is accepted from these into the target format(Override this!)
    acceptto = [] #List of formats; conversion is accepted from the target format into these (Override this!)
    
    label = "(ERROR: label not overriden from AbstractConverter!)" #Override this with a sensible name
    
    def __init__(self, id, **kwargs):        
        if 'label' in kwargs:
            self.id = id
            self.label = kwargs['label']
            
    def convertforinput(self,filepath, metadata):        
        """Convert from target format into one of the source formats. Relevant if converters are used in InputTemplates. Metadata already is metadata for the to-be-generated file. 'filepath' is both the source and the target file, the source file will be erased and overwritten with the conversion result!"""        
        
        assert isinstance(metadata, CLAMMetaData) #metadata of the destination file (file to be generated here)        
        if not metadata.__class__ in self.acceptto:
            raise Exception("Convertor " + self.__class__.__name__ + " can not convert input files to " + metadata.__class__.__name__ + "!")
        return False #Return True on success, False on failure
        
    def convertforoutput(self,outputfile):
        """Convert from one of the source formats into target format. Relevant if converters are used in OutputTemplates. Sourcefile is a CLAMOutputFile instance."""    
        assert isinstance(outputfile, CLAMMetaData) #metadata of the destination file (file to be generated here)        
        if not metadata.__class__ in self.acceptfrom:
            raise Exception("Convertor " + self.__class__.__name__ + " can not convert input files to " + metadata.__class__.__name__ + "!")
        return [] #Return converted contents (must be an iterable) or raise an exception on error
        
class CharEncodingConverter(AbstractConverter):
    acceptfrom = acceptto = [clam.common.formats.PlainTextFormat]
    
    label = "CharEncodingConverter" #to be overriden in instance creation
    
    def __init__(self, id,  **kwargs):
        if not 'label' in kwargs:
            raise Exception("No label specified for EncodingConvertor!")
        
        if 'fromcharset' in kwargs:
            self.charset = kwargs['fromcharset']
        elif 'tocharset' in kwargs:            
            self.charset = kwargs['tocharset']
        elif 'charset' in kwargs:
            self.charset = kwargs['charset']    
        else:
            raise Exception("No charset specified for EncodingConvertor!")

        super(EncodingConvertor,self).__init__(**kwargs)
      
    def convertforinput(self,filepath, metadata=None):
        """Convert from target format into one of the source formats. Relevant if converters are used in InputTemplates. Metadata already is metadata for the to-be-generated file."""
        super(EncodingConvertor,self).__init_( **kwargs)
        
        os.copy(filepath, filepath + '.convertsource')
        
        try:
            fsource = codecs.open(filepath + '.convertsource','r',self.charset)
            ftarget = codecs.open(filepath,'w',metadata['encoding'])
            for line in fsource:
                ftarget.write(line + "\n")
        except:
            ftarget.close()
            fsource.fclose()
        
        os.unlink(filepath + '.convertsource')
        
        
    def convertforoutput(self,outputfile):
        """Convert from one of the source formats into target format. Relevant if converters are used in OutputTemplates. Outputfile is a CLAMOutputFile instance."""    
        super(EncodingConvertor,self).__init_( **kwargs)
        
        web.header('Content-Type', 'text/plain; charset=' + self.charset)
        for line in outputfile:
            yield line.encode(self.charset)
        
        

