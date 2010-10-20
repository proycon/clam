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


######### NEW ################
class PlainText(CLAMMetaData):
    attributes = {'encoding':True,'language':False } #attributes with True are always required!
    mimetype = "text/plain"

    def __init__(self, **kwargs):
        super(PlainTextFormat,self).__init__(**kwargs)

######### OLD ################

import re
from lxml import etree as ElementTree
from StringIO import StringIO
from clam.common.viewers import AbstractViewer
from clam.common.parameters import AbstractParameter
from clam.common.languages import languagename


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
        for extensionnode in node:
            if extensionnode.tag == 'extension':
                extensions.append(extensionnode.text)
        return globals()[node.tag](encoding, extensions) #return format instance
    else:
        raise Exception("No such format exists: " + node.tag)


class AbstractProfiler(object):
    def __init__(self, **kwargs):
        if 'paramconditions' in kwargs:
            self.paramconditions = kwargs['paramconditions']
        else:
            self.paramconditions = lambda params: True

    def profile(self, inputfiles, parameters):
        """Compute a profile: a list of (filename, Format) tuples describing all files that will be outputted given a set of inputfiles (also a list of (filename, Format) tuples), and all set parameters (a dictionary of parameter IDs and associated values)""" 
        return []


class OneToOneProfiler(AbstractProfiler):
    def __init__(self,inputformat, outputformat, **kwargs ):
        assert isinstance(inputformat, Format)
        if not inputformat.extension:
            raise ValueError("Input format must have an extension defined")
        self.inputformat = inputformat
        assert isinstance(outputformat, Format) and outputformat.extension
        if not outputformat.extension:
            raise ValueError("Input format must have an extension defined")
        self.outputformat = outputformat
        super(OneToOneProfiler,self).__init__(**kwargs)

    def profile(self, inputfiles, parameters):
        profile = []
        if self.paramconditions(parameters):
            for inputfilename, inputformat in inputfiles:
                if inputformat == self.inputformat:
                    if inputfilename.endswith('.' + inputformat.extension):
                        outputfilename = inputfilename[-len(inputformat.extension):] + outputformat.extension
                        profile.append(outputfilename, self.outputformat)
        return profile

class NoneToOneProfiler(AbstractProfiler):
    def __init__(self, filename, format):
        self.filename = filename
        assert isinstance(format, Format)
        self.format = format

    def profile(self, inputfiles, parameters):
        return [(self.filename, self.format)]




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

    encodings = None #list of all allowed encodings (unrestricted if set to None)
    languages = None #list of all allowed languages (unrestricted if set to None)
    

    def __init__(self,**kwargs ):
        self.encoding = None
        self.language = None
        self.extension = None
        self.subdirectory = '' #Extract all files of this time into this subdirectory
        self.archivesubdirs = True #Retain subdirectories from archives?
        self.viewers = []
        

        for key, value in kwargs.items():
            if key == 'mask':
                self.mask = re.compile(value) #in case extensions aren't enough
            elif key == 'encoding':
                self.encoding = value
            elif key == 'language':
                self.language = value
            elif key == 'extension':
                self.extension = value
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
        s = self.name
        if self.language:
            s += ', ' + languagename(self.language)
        if self.encoding:
            s += ' ['+self.encoding+']'
        return s

    def unicode(self):
        """Returns a string representation of this format"""
        s = self.name
        if self.language:
            s += ', ' + languagename(self.language)
        if self.encoding:
            s += ' ['+self.encoding+']'
        return s



class PlainTextFormat(Format):
    
    name = "Plain Text Format"
    mimetype = 'text/plain'

    def __init__(self, **kwargs ):
        super(PlainTextFormat,self).__init__(**kwargs)
        
                
class TokenizedTextFormat(Format):    
    
    name = "Tokenised Plain Text Format"
    mimetype = 'text/plain'

    def __init__(self, **kwargs ):
        super(TokenizedTextFormat,self).__init__(**kwargs)


class VerboseTokenizedTextFormat(Format):    
    
    name = "Verbosely Tokenised Text Format (Frog)"
    mimetype = 'text/plain'

    def __init__(self, **kwargs ):
        super(VerboseTokenizedTextFormat,self).__init__(**kwargs)



                
class TadpoleFormat(Format):    
    
    name = "Tadpole Output Format"
    mimetype = 'text/plain'

    def __init__(self, **kwargs ):
        super(TadpoleFormat,self).__init__(**kwargs)



class DCOIFormat(Format):    
    
    name = "DCOI format"
    mimetype = 'text/xml'

    def __init__(self, **kwargs):
        super(DCOIFormat,self).__init__(**kwargs)


class KBXMLFormat(Format):
    
    name = "Koninklijke Bibliotheek XML-formaat"
    mimetype = 'text/xml'

    def __init__(self, **kwargs ):
        super(KBXMLFormat,self).__init__(encoding, extensions, **kwargs)

