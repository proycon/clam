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
from clam.common.viewers import AbstractViewer

def formatfromxml(node): #TODO: Add viewers
    if not isinstance(node,ElementTree._Element):
        node = ElementTree.parse(StringIO(node)).getroot()
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

    """This is the base Format class. Inherit from this class to create new format definitions.
    The class should have a 'name' member, containing the name the users will see. Upon instantiation,
    Multiple extensions may be associated with the format, but first will be the extension that will be
    automatically assigned when the user uploads a file in this format. In addition, an encoding will
    have to be specified.

    There are several keyword arguments:
            mask : a regular expression for recognising file, in case extensions aren't enough. Files matching 
                   this mask will be considered to be in this format
            subdirectory = ''        If not empty, confines all uploaded files of
                                     this format to a specific subdirectory.
                                     (Only makes sense for INPUT formats)
            archivesubdirs = True    If set to False, all subdirectories in an uploaded archive will
                                     be squashed, extracting all its files to the base output directory.
                                     (Only makes sense for INPUT formats)
            viewers = []             A list of Viewer-derived instances, association particular 
                                     Viewers or Visualisation Modules with this format.

    Note that there are methods you may want to overrule in your inherited format!
    """

    name = "Unspecified Format"
    mask = None

    def __init__(self,encoding = 'utf-8', extensions = [], **kwargs ):
        if isinstance(extensions,list):
            self.extensions = extensions
        else:
            self.extensions =  [ extensions ]
        self.encoding = encoding
        self.subdirectory = '' #Extract all files of this time into this subdirectory
        self.archivesubdirs = True #Retain subdirectories from archives?
        self.viewers = []
        for key, value in kwargs.items():
            if key == 'mask':
                self.mask = re.compile(value) #in case extensions aren't enough
            elif key == 'subdirectory':
                self.subdirectory = value
            elif key == 'archivesubdirs':
                self.archivesubdirs = value
            elif key == 'viewer':
                assert isinstance(value, AbstractViewer)
                self.viewers.append(value)
            elif key == 'viewers':
                for x in value:
                    assert isinstance(x, AbstractViewer)
                self.viewers = value #TODO: implement
            #elif key == 'numberfiles': #for future use?
                
            

    def validate(self,filename):
        """This is a validation function for this format, it is passed the filename of 
        the file to be validated, and should return True if the file is indeed a valid
        file in this format, and False otherwise. Overload this method in your own class,
        as by default it always returns True."""
        return True

    def match(self,filename):
        """Checks if the specified file match the defined extensions/mask? There's usually no need to overload this in inherited classes.""" 
        for extension in self.extensions:
            if filename[ -1 * len(extension) - 1:] == '.' + extension:
                return True
        if self.mask:
            return re.match(filename)
        else:
            return False
        
    def filename(self,filename):
        """Rename this file so it matches the defined extension, return the new filename. There's usually no need to overload this in inherited classes."""
        if not self.match(filename):
            for ext in self.extensions[0].split("."):
                if filename[-1 * len(ext):] == ext:
                    filename = filename[:-1 * len(ext)]
            return filename + '.' + self.extensions[0]
        else:
            return filename

    def xml(self):
        """Returns an XML representation of the Format definition"""
        xml = "<" + self.__class__.__name__
        xml += ' name="'+unicode(self.name) + '"'
        xml += ' encoding="'+self.encoding + '"'
        if self.mask:
            xml += ' mask="'+self.mask + '"'
        xml += '>'
        for extension in self.extensions:
            xml += " <extension>" + extension + "</extension>"     
        if self.viewers:
            xml += "<viewers>"
            for viewer in self.viewers:
                xml += "<" + viewer.__class__.__name__ + " id=\""+viewer.id+"\" name=\""+viewer.name+"\" />"
            xml += "</viewers>"
        xml += "</" + self.__class__.__name__ + ">"
        return xml

    def str(self):
        """Returns a string representation of this format"""
        if self.encoding:
            return self.name + ' ['+self.encoding+']'
        else:
            return self.name

    def unicode(self):
        """Returns a string representation of this format"""
        if self.encoding:
            return self.name + ' ['+self.encoding+']'
        else:
            return self.name

class PlainTextFormat(Format):    
    
    name = "Plain Text Format (not tokenised)"

    def __init__(self,encoding = 'utf-8', extensions = ['txt'], **kwargs ):
        super(PlainTextFormat,self).__init__(encoding, extensions, **kwargs)

                
class TokenizedTextFormat(Format):    
    
    name = "Plain Text Format (already tokenised)"

    def __init__(self,encoding = 'utf-8', extensions = ['tok.txt'], **kwargs ):
        super(TokenizedTextFormat,self).__init__(encoding, extensions, **kwargs)



                
class TadpoleFormat(Format):    
    
    name = "Tadpole Output Format"

    def __init__(self,encoding = 'utf-8', extensions = ['tadpole.out'], **kwargs ):
        super(TadpoleFormat,self).__init__(encoding, extensions, **kwargs)


class DCOIFormat(Format):    
    
    name = "Log format (not further defined)"

    def __init__(self,encoding = 'utf-8', extensions = ['log'], **kwargs):
        super(DCOIFormat,self).__init__(encoding, extensions, **kwargs)




class DCOIFormat(Format):    
    
    name = "SoNaR/DCOI format"

    def __init__(self,encoding = 'utf-8', extensions = ['dcoi.xml','sonar.xml'], **kwargs):
        super(DCOIFormat,self).__init__(encoding, extensions, **kwargs)


class KBXMLFormat(Format):    
    
    name = "Koninklijke Bibliotheek XML-formaat"

    def __init__(self,encoding = 'utf-8', extensions = ['xml'], **kwargs ):
        super(KBXMLFormat,self).__init__(encoding, extensions, **kwargs)



