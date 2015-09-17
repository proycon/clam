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


from clam.common.data import CLAMMetaData  #import CLAMMetaData


###############################################################################################################################################
#       Format Definitions
###############################################################################################################################################

class ExampleFormat(CLAMMetaData):
    """This is an Example format, please inspect its source code if you want to create custom formats!"""

    #A dictionary of attributes that this format can take, the keys correspond
    #to the attributes, the values can be either:
    # True   - Accept any value, this attribute is required
    # False  - Accept any value, but this attribute is not required
    # a list - Accept any of the specified values (if False is a member then this attribute is not required)
    # a specific value - Simply always assign this static value
    #attributes = {'encoding':True, 'language':False, 'colour': ['green','red','blue'], 'pi':3.14 }

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

    attributes = {'encoding':True,'language':False }
    mimetype = "text/plain"

    def httpheaders(self):
        """HTTP headers to output for this format. Yields (key,value) tuples."""
        yield ("Content-Type", self.mimetype + "; charset=" + self['encoding'])

class HTMLFormat(CLAMMetaData):
    """HTML Format Definition. This format has one required attribute: encoding"""
    attributes = {'encoding':True,'language':False }
    mimetype = "text/html"

    def httpheaders(self):
        """HTTP headers to output for this format. Yields (key,value) tuples."""
        yield ("Content-Type", self.mimetype + "; charset=" + self['encoding'])

class BinaryDataFormat(CLAMMetaData):
    attributes = {}
    name = "Application-specific Binary Data"
    mimetype = 'application/octet-stream'

class TadpoleFormat(CLAMMetaData):
    attributes = {'tokenisation':'yes','lemmatisation':['yes','no'],'postagging':['yes','no'],'morphologicalanalysis':['yes','no'],'mwudetection':['yes','no'],'parsing':['yes','no'] }
    name = "Tadpole Columned Output Format"
    mimetype = 'text/plain'

class CSVFormat(CLAMMetaData):
    attributes = {'encoding':True,'language':False }
    name = "Comma separated file"
    mimetype = 'text/csv'

class UndefinedXMLFormat(CLAMMetaData):
    name = "Undefined XML Format"
    mimetype = 'text/xml'
    scheme = ''

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

