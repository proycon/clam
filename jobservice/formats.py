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

import re

class Format(object):

    name = "Unspecified Format"
    mask = None

    def __init__(self,encoding = 'utf-8', extensions = [], mask = None):
        if isinstance(extensions,list):
            self.extensions = extensions
        else:
            self.extensions =  [ extensions ]
        self.encoding = encoding
        if mask:
            self.mask = re.compile(mask) #in case extensions aren't enough

    def validate(self,filename):
        return True

    def match(self,filename):
        """Does this file match the defined extensions/mask?""" 
        for extension in self.extensions:
            if filename[ -1 * len(extension) - 1:] == '.' + extension:
                return True
        if self.mask:
            return r.match(filename)
        else:
            return False
        
    def filename(self,filename):
        """Rename this file so it matches the defined extension"""
        if not self.match(filename)
            for ext in self.extensions[0].split("."):
                if filename[-1 * len(ext):] == ext:
                    filename = filename[:-1 * len(ext)]
            return filename + '.' + self.extensions[0]
        else:
            return filename


class PlainTextFormat(Format):    
    
    name = "Plain Text Format (not tokenised)"

    def __init__(self,encoding = 'utf-8', extensions = ['txt'], mask = None):
        super(PlainTextFormat,self).__init__(id,encoding, extensions, mask)


                
class TokenizedTextFormat(Format):    
    
    name = "Plain Text Format (already tokenised)"

    def __init__(self,encoding = 'utf-8', extensions = ['tok.txt'], mask = None):
        super(TokenizedTextFormat,self).__init__(id,encoding, extensions, mask)



class DCOIFormat(Format):    
    
    name = "SoNaR/DCOI format"

    def __init__(self,encoding = 'utf-8', extensions = ['dcoi.xml','sonar.xml'], mask = None):
        super(DCOIFormat,self).__init__(id,encoding, extensions, mask)


    
                               
