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
from lxml import etree as ElementTree
from StringIO import StringIO

def formatfromxml(node):
    if not isinstance(node,ElementTree._Element):
        node = ElementTree.parse(StringIO(node)).getroot() #verify this works? (may need .root?) 
    if node.tag in globals():
        encoding = 'utf-8'
        extensions = []
        mask = None
        for attrib, value in node.attrib.items():
            if attrib == 'encoding':
                encoding = value
            elif attrib == 'mask':
                mask = value
        for extensionnode in node:
            if extensionnode.tag == 'extension':
                extensions.append(extensionnode.value)            
        return globals()[node.tag](encoding, extensions, mask) #return format instance
    else:
        raise Exception("No such format exists: " + node.tag)

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
            return re.match(filename)
        else:
            return False
        
    def filename(self,filename):
        """Rename this file so it matches the defined extension"""
        if not self.match(filename):
            for ext in self.extensions[0].split("."):
                if filename[-1 * len(ext):] == ext:
                    filename = filename[:-1 * len(ext)]
            return filename + '.' + self.extensions[0]
        else:
            return filename

    def xml(self):
        xml = "<" + self.__class__.__name__
        xml += ' name="'+self.name + '"'
        xml += ' encoding="'+self.encoding + '"'
        if self.mask:
            xml += ' mask="'+self.mask + '"'
        xml += '>'
        for extension in self.extensions:
            xml += " <extension>" + extension + "</extension>"     
        xml += "</" + self.__class__.__name__ + ">"
        return xml


class PlainTextFormat(Format):    
    
    name = "Plain Text Format (not tokenised)"

    def __init__(self,encoding = 'utf-8', extensions = ['txt'], mask = None):
        super(PlainTextFormat,self).__init__(encoding, extensions, mask)


                
class TokenizedTextFormat(Format):    
    
    name = "Plain Text Format (already tokenised)"

    def __init__(self,encoding = 'utf-8', extensions = ['tok.txt'], mask = None):
        super(TokenizedTextFormat,self).__init__(encoding, extensions, mask)



class DCOIFormat(Format):    
    
    name = "SoNaR/DCOI format"

    def __init__(self,encoding = 'utf-8', extensions = ['dcoi.xml','sonar.xml'], mask = None):
        super(DCOIFormat,self).__init__(encoding, extensions, mask)


