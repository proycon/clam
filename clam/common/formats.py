###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Format classes --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/clam
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       Licensed under GPLv3
#
###############################################################

from __future__ import print_function, unicode_literals, division, absolute_import


from clam.common.parameters import StringParameter, StaticParameter, ChoiceParameter
from clam.common.data import CLAMMetaData  #import CLAMMetaData


###############################################################################################################################################
#       Format Definitions
###############################################################################################################################################

class ExampleFormat(CLAMMetaData):
    """This is an Example format, please inspect its source code if you want to create custom formats!"""

    #Attributes is a dictionary that maps to parameter instances, these parameters express the possible metadata values, along with whether these are required or not
    attributes = {}

    #Do you want to allow any other custom attributes? Defined by the InputTemplate/OutputTemplate
    allowcustomattributes = True

    #Specify a mimetype for your format
    mimetype = "text/plain"


    #If your format is XML-based, specify a scheme:
    scheme = None

    #NOTE: Never override the constructor with different arguments!

    def validate(self):
        """Add your validation method here, should return True or False"""
        return True

    def loadinlinemetadata(self):
        """If there is metadata IN the actual file, this method should extract it and assign it to this object. Will be automatically called from constructor. Note that the file (CLAMFile) is accessible through self.file"""
        pass

    def saveinlinemetadata(self):
        """If there is metadata that should be IN the actual file, this method can store it. Note that the file (CLAMFile) is accessible through self.file"""
        pass

    def httpheaders(self):
        """HTTP headers to output for this format. Yields (key,value) tuples."""
        yield ("Content-Type", self.mimetype)


class PlainTextFormat(CLAMMetaData):
    """Plain Text Format Definition. This format has one required attribute: encoding"""

    name = "Plain Text Format"
    attributes = {
        'encoding': StringParameter('encoding', "Character Encoding",required=True),
        'language': StringParameter('language', "Language", required=False),
    }
    mimetype = "text/plain"

    def httpheaders(self):
        """HTTP headers to output for this format. Yields (key,value) tuples."""
        yield ("Content-Type", self.mimetype + "; charset=" + self['encoding'])

class HTMLFormat(CLAMMetaData):
    """HTML Format Definition. This format has one required attribute: encoding"""
    name = "HTML Format"
    attributes = {
        'encoding': StringParameter('encoding', "Character Encoding",required=True),
        'language': StringParameter('language', "Language", required=False),
    }
    mimetype = "text/html"

    def httpheaders(self):
        """HTTP headers to output for this format. Yields (key,value) tuples."""
        yield ("Content-Type", self.mimetype + "; charset=" + self['encoding'])

class BinaryDataFormat(CLAMMetaData):
    attributes = {}
    name = "Application-specific Binary Data"
    mimetype = 'application/octet-stream'

class FrogTSVFormat(CLAMMetaData):
    attributes = {
        'tokenisation': StaticParameter('tokenisation','Tokenisation',value="yes", required=False),
        'postagging': ChoiceParameter('postagging','Part-of-Speech tagging',"Part-of-Speech tagging",choices=['yes','no'],required=False),
        'lemmatisation': ChoiceParameter('lemmatisation','Lemmatisation', "Lemmatisation", choices=['yes','no'],required=False),
        'morphologicalanalysis': ChoiceParameter('morphologicalanalysis','Morphology',"Morphology", choices=['yes','no'],required=False),
        'mwudetection': ChoiceParameter('mwudetection','Multi-Word Unit Detection',"MWU Detection", choices=['yes','no'],required=False),
        'parsing': ChoiceParameter('parsing','Dependency Parsing',"Dependency Parsing", choices=['yes','no'],required=False),
        'chunking': ChoiceParameter('chunking','Chunking',"Chunking", choices=['yes','no'],required=False),
        'namedentities': ChoiceParameter('namedentities','Named Entities',"Named Entities", choices=['yes','no'],required=False),
     }
    name = "Frog Tab Separated Values"
    mimetype = 'text/plain'
TadpoleFormat = FrogTSVFormat #backwardcompatibility

class CSVFormat(CLAMMetaData):
    attributes = {
        'encoding': StringParameter('encoding', "Character Encoding",required=True),
        'language': StringParameter('language', "Language", required=False),
    }
    name = "Comma Separated Values"
    mimetype = 'text/csv'

class XMLFormat(CLAMMetaData):
    name = "XML Format (generic, not further specified)"
    mimetype = 'text/xml'
    scheme = ''
UndefinedXMLFormat = XMLFormat #backward compatibility

class JSONFormat(CLAMMetaData):
    name = "JSON Format (generic, not further specified)"
    mimetype = 'application/json'

class FoLiAXMLFormat(CLAMMetaData):
    attributes = {}
    name = "FoLiA XML"
    mimetype = 'text/xml'
    scheme = '' #TODO

class AlpinoXMLFormat(CLAMMetaData):
    attributes = {}
    name = "Alpino XML"
    mimetype = 'text/xml'
    scheme = '' #TODO

class DCOIFormat(CLAMMetaData):
    attributes = {}
    name = "DCOI format"
    mimetype = 'text/xml'
    scheme = '' #TODO


class KBXMLFormat(CLAMMetaData):
    name = "Koninklijke Bibliotheek XML-formaat"
    mimetype = 'text/xml'
    scheme = '' #TODO


class TICCLVariantOutputXML(CLAMMetaData):
    name="Ticcl Variant Output"
    mimetype='text/xml'
    scheme='' #TODO

class TICCLShadowOutputXML(CLAMMetaData):
    name="Ticcl Shadow Output"
    mimetype='text/xml'
    scheme='' #TODO

class MSWordFormat(CLAMMetaData):
    attributes = {}
    name = "Microsoft Word format"
    mimetype = 'application/msword'
    scheme = '' #TODO

class PDFFormat(CLAMMetaData):
    attributes = {}
    name = "PDF"
    mimetype = 'application/pdf'

class OpenDocumentTextFormat(CLAMMetaData):
    attributes = {}
    name = "Open Document Text Format"
    mimetype = 'application/vnd.oasis.opendocument.text'

class ZIPFormat(CLAMMetaData):
    attributes = {}
    name = "ZIP Archive"
    mimetype = 'application/zip'

class XMLStyleSheet(CLAMMetaData):
    attributes = {}
    name = "XML Stylesheet"
    mimetype ='application/xslt+xml'

class WaveAudioFormat(CLAMMetaData):
    attributes = {}
    name ="Wave Audio File"
    mimetype = 'audio/wav'

class OggAudioFormat(CLAMMetaData):
    attributes = {}
    name ="Ogg Audio File"
    mimetype = 'audio/ogg'

class MP3AudioFormat(CLAMMetaData):
    attributes = {}
    name ="MP3 Audio File"
    mimetype = 'audio/mpeg'

class MpegVideoFormat(CLAMMetaData):
    attributes = {}
    name ="Mpeg Video"
    mimetype = 'video/mpeg'

class OggVideoFormat(CLAMMetaData):
    attributes = {}
    name ="Ogg Video File"
    mimetype = 'audio/ogg'

class PngImageFormat(CLAMMetaData):
    attributes = {}
    name ="PNG Image"
    mimetype = 'image/png'

class JpegImageFormat(CLAMMetaData):
    attributes = {}
    name ="Jpeg Image"
    mimetype = 'image/jpeg'

class GifImageFormat(CLAMMetaData):
    attributes = {}
    name ="Gif Image"
    mimetype = 'image/gif'

class TiffImageFormat(CLAMMetaData):
    attributes = {}
    name ="Tiff Image"
    mimetype = 'image/tiff'

class DjVuFormat(CLAMMetaData):
    attributes = {}
    name = "DjVu format"
    mimetype = 'image/x-djvu'

