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

    schemaorg_type = "DigitalDocument"


    #If your format is XML-based, specify a schema:
    schema = None

    #NOTE: Never override the constructor with different arguments!

    def validator(self):
        """Implement your validator here, should return True or False. Additionaly, if there is metadata IN the actual file, this method should extract it and assign it to this object. Will be automatically called from constructor. Note that the file (CLAMFile) is accessible through self.file, which is guaranteerd to exist when this method is called."""
        return True

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
    schemaorg_type = "TextDigitalDocument"

    def httpheaders(self):
        """HTTP headers to output for this format. Yields (key,value) tuples."""
        yield ("Content-Type", self.mimetype + "; charset=" + self['encoding'])

class BinaryDataFormat(CLAMMetaData):
    attributes = {}
    name = "Application-specific Binary Data"
    mimetype = 'application/octet-stream'
    schemaorg_type = "DigitalDocument"

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
    schemaorg_type = "TextDigitalDocument"

TadpoleFormat = FrogTSVFormat #backwardcompatibility

class CSVFormat(CLAMMetaData):
    attributes = {
        'encoding': StringParameter('encoding', "Character Encoding",required=True),
        'language': StringParameter('language', "Language", required=False),
    }
    name = "Comma Separated Values"
    mimetype = 'text/csv'
    schemaorg_type = "SpreadsheetDigitalDocument"

class XMLFormat(CLAMMetaData):
    name = "XML Format (generic, not further specified)"
    mimetype = 'text/xml'
    schema = ''
    schemaorg_type = "DigitalDocument"
UndefinedXMLFormat = XMLFormat #backward compatibility

class JSONFormat(CLAMMetaData):
    name = "JSON Format (generic, not further specified)"
    mimetype = 'application/json'
    schemaorg_type = "DigitalDocument"

class FoLiAXMLFormat(CLAMMetaData):
    attributes = { #TODO: this is not complete yet
        'version': StringParameter("version", "Version", "The FoLiA version", required=False),
        'text-annotation': StringParameter("text-annotation","Token Annotation","Comma separated list of text annotation sets present, may also be set to the value 'no-set'.", required=False),
        'token-annotation': StringParameter("token-annotation","Token Annotation","Comma separated list of token annotation sets present, may also be set to the value 'no-set'.", required=False),
        'sentence-annotation': StringParameter("sentence-annotation","Sentence Annotation","Comma separated list of sentence annotation sets present, may also be set to the value 'no-set'.", required=False),
        'paragraph-annotation': StringParameter("paragraph-annotation","Paragraph Annotation","Comma separated list of paragraph annotation sets present, may also be set to the value 'no-set'.", required=False),
        'pos-annotation': StringParameter("pos-annotation","Part-of-Speech Annotation","Comma separated list of part-of-speech sets present, may also be set to the value 'no-set'.", required=False),
        'lemma-annotation': StringParameter("lemma-annotation","Lemma Annotation","Comma separated list of lemma sets present, may also be set to the value 'no-set'.", required=False),
        'sense-annotation': StringParameter("sense-annotation","Sense Annotation","Comma separated list of sense sets present, may also be set to the value 'no-set'.", required=False),
        'entity-annotation': StringParameter("entity-annotation","Entity Annotation","Comma separated list of entity sets present, may also be set to the value 'no-set'.", required=False),
        'syntax-annotation': StringParameter("syntax-annotation","Syntax Annotation","Comma separated list of syntax sets present, may also be set to the value 'no-set'.", required=False),
        'chunk-annotation': StringParameter("chunk-annotation","Chunk Annotation","Comma separated list of chunk sets present, may also be set to the value 'no-set'.", required=False),
        'relation-annotation': StringParameter("relation-annotation","Relation Annotation","Comma separated list of relation sets present, may also be set to the value 'no-set'.", required=False),
    }
    name = "FoLiA XML"
    mimetype = 'text/xml'
    schema = '' #TODO
    schemaorg_type = "TextDigitalDocument"

    def validator(self):
        try:
            import folia.main as folia #soft-dependency, not too big a deal if it is not present, but no metadata extraction then

            #this loads a whole FoLiA document into memory! which is a bit of a waste of memory and a performance hog!
            try:
                doc = folia.Document(file=str(self.file))
            except Exception as e:
                self['validation_error'] = str(e)
                self.valid = False
                return False
            self['version'] = doc.version
            for annotationtype, annotationset in doc.annotations:
                key = folia.annotationtype2str(annotationtype).lower() + "-annotation"
                if annotationset is None: annotationset = "no-set"
                if key in self and annotationset not in [ x.strip() for x in self[key].split(',') ]:
                    self[key] += "," +  annotationset
                else:
                    self[key] = annotationset
        except ImportError as e:
            self['validation_error'] = str(e)
            return False

        return True

class AlpinoXMLFormat(CLAMMetaData):
    attributes = {}
    name = "Alpino XML"
    mimetype = 'text/xml'
    schema = '' #TODO
    schemaorg_type = "TextDigitalDocument"

class DCOIFormat(CLAMMetaData):
    attributes = {}
    name = "DCOI format"
    mimetype = 'text/xml'
    schema = '' #TODO
    schemaorg_type = "TextDigitalDocument"


class KBXMLFormat(CLAMMetaData):
    name = "Koninklijke Bibliotheek XML-formaat"
    mimetype = 'text/xml'
    schema = '' #TODO
    schemaorg_type = "TextDigitalDocument"


class TICCLVariantOutputXML(CLAMMetaData):
    name="Ticcl Variant Output"
    mimetype='text/xml'
    schema='' #TODO
    schemaorg_type = "TextDigitalDocument"

class TICCLShadowOutputXML(CLAMMetaData):
    name="Ticcl Shadow Output"
    mimetype='text/xml'
    schema='' #TODO
    schemaorg_type = "TextDigitalDocument"

class MSWordFormat(CLAMMetaData):
    attributes = {}
    name = "Microsoft Word format"
    mimetype = 'application/msword'
    schema = '' #TODO
    schemaorg_type = "TextDigitalDocument"

class PDFFormat(CLAMMetaData):
    attributes = {}
    name = "PDF"
    mimetype = 'application/pdf'
    schemaorg_type = "TextDigitalDocument"

class OpenDocumentTextFormat(CLAMMetaData):
    attributes = {}
    name = "Open Document Text Format"
    mimetype = 'application/vnd.oasis.opendocument.text'
    schemaorg_type = "TextDigitalDocument"

class ZIPFormat(CLAMMetaData):
    attributes = {}
    name = "ZIP Archive"
    mimetype = 'application/zip'
    schemaorg_type = "Dataset"

class XMLStyleSheet(CLAMMetaData):
    attributes = {}
    name = "XML Stylesheet"
    mimetype ='application/xslt+xml'
    schemaorg_type = "DigitalDocument"

class WaveAudioFormat(CLAMMetaData):
    attributes = {}
    name ="Wave Audio File"
    mimetype = 'audio/vnd.wave'
    schemaorg_type = "AudioObject"

class OggAudioFormat(CLAMMetaData):
    attributes = {}
    name ="Ogg Vorbis Audio File"
    mimetype = 'audio/vorbis'
    schemaorg_type = "AudioObject"

class MP3AudioFormat(CLAMMetaData):
    attributes = {}
    name ="MP3 Audio File"
    mimetype = 'audio/mpeg'
    schemaorg_type = "AudioObject"

class MpegVideoFormat(CLAMMetaData):
    attributes = {}
    name ="Mpeg Video"
    mimetype = 'video/mpeg'
    schemaorg_type = "VideoObject"

class OggVideoFormat(CLAMMetaData):
    attributes = {}
    name ="Ogg Video File"
    mimetype = 'audio/ogg'
    schemaorg_type = "VideoObject"

class PngImageFormat(CLAMMetaData):
    attributes = {}
    name ="PNG Image"
    mimetype = 'image/png'
    schemaorg_type = "ImageObject"

class JpegImageFormat(CLAMMetaData):
    attributes = {}
    name ="Jpeg Image"
    mimetype = 'image/jpeg'
    schemaorg_type = "ImageObject"

class GifImageFormat(CLAMMetaData):
    attributes = {}
    name ="Gif Image"
    mimetype = 'image/gif'
    schemaorg_type = "ImageObject"

class TiffImageFormat(CLAMMetaData):
    attributes = {}
    name ="Tiff Image"
    mimetype = 'image/tiff'
    schemaorg_type = "ImageObject"

class DjVuFormat(CLAMMetaData):
    attributes = {}
    name = "DjVu format"
    mimetype = 'image/x-djvu'
    schemaorg_type = "ImageObject"

