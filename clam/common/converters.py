###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Converters --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/clam
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       Licensed under the GNU Public License v3
#
###############################################################

#pylint: disable=redefined-builtin

from __future__ import print_function, unicode_literals, division, absolute_import

import shutil
import io
import os
import flask
from clam.common.data import CLAMMetaData, CLAMOutputFile
from clam.common.util import withheaders
import clam.common.formats

class AbstractConverter(object):
    acceptforinput = [] #List of formats; accept the following formats as target for conversion of input
    acceptforoutput = [] #List of formats; accept the following formats as source for conversion for output

    label = "(ERROR: label not overriden from AbstractConverter!)" #Override this with a sensible name

    def __init__(self, id, **kwargs):
        if 'label' in kwargs:
            self.id = id
            self.label = kwargs['label']

    def convertforinput(self,filepath, metadata):
        """Convert from target format into one of the source formats. Relevant if converters are used in InputTemplates. Metadata already is metadata for the to-be-generated file. 'filepath' is both the source and the target file, the source file will be erased and overwritten with the conversion result!"""
        assert isinstance(metadata, CLAMMetaData) #metadata of the destination file (file to be generated here)
        if not metadata.__class__ in self.acceptforinput:
            raise Exception("Convertor " + self.__class__.__name__ + " can not convert input files to " + metadata.__class__.__name__ + "!")
        return False #Return True on success, False on failure

    def convertforoutput(self,outputfile):
        """Convert from one of the source formats into target format. Relevant if converters are used in OutputTemplates. Sourcefile is a CLAMOutputFile instance."""
        assert isinstance(outputfile, CLAMOutputFile) #metadata of the destination file (file to be generated here)
        if not outputfile.metadata.__class__ in self.acceptforoutput:
            raise Exception("Convertor " + self.__class__.__name__ + " can not convert input files to " + outputfile.metadata.__class__.__name__ + "!")
        return [] #Return converted contents (must be an iterable) or raise an exception on error

class CharEncodingConverter(AbstractConverter):
    acceptforinput = acceptforoutput = [clam.common.formats.PlainTextFormat]

    label = "CharEncodingConverter" #to be overriden in instance creation

    def __init__(self, id,  **kwargs):
        if 'label' not in kwargs:
            raise Exception("No label specified for EncodingConvertor!")

        if 'fromcharset' in kwargs:
            self.charset = kwargs['fromcharset']
        elif 'tocharset' in kwargs:
            self.charset = kwargs['tocharset']
        elif 'charset' in kwargs:
            self.charset = kwargs['charset']
        else:
            raise Exception("No charset specified for EncodingConvertor!")

        super(CharEncodingConverter,self).__init__(id, **kwargs)

    def convertforinput(self,filepath, metadata=None):
        """Convert from target format into one of the source formats. Relevant if converters are used in InputTemplates. Metadata already is metadata for the to-be-generated file."""
        super(CharEncodingConverter,self).convertforinput(filepath, metadata)

        shutil.copy(filepath, filepath + '.convertsource')

        try:
            fsource = io.open(filepath + '.convertsource','r',encoding=self.charset)
            ftarget = io.open(filepath,'w',encoding=metadata['encoding'])
            for line in fsource:
                ftarget.write(line + "\n")
            success = True
        except:
            ftarget.close()
            fsource.fclose()
            success = False
        finally:
            os.unlink(filepath + '.convertsource')

        return success


    def convertforoutput(self,outputfile):
        """Convert from one of the source formats into target format. Relevant if converters are used in OutputTemplates. Outputfile is a CLAMOutputFile instance."""
        super(CharEncodingConverter,self).convertforoutput(outputfile)

        return withheaders( flask.make_response( ( line.encode(self.charset) for line in outputfile ) ) , 'text/plain; charset=' + self.charset)



class PDFtoTextConverter(AbstractConverter):
    acceptforinput = [clam.common.formats.PlainTextFormat]

    converttool = 'pdftotext'

    def __init__(self, id,  **kwargs):
        super(PDFtoTextConverter,self).__init__(id, **kwargs)


    def convertforinput(self,filepath, metadata=None):
        super(PDFtoTextConverter,self).convertforinput(filepath, metadata)

        shutil.copy(filepath, filepath + '.convertsource.pdf')
        returncode = os.system(self.converttool + ' -layout ' + filepath + '.convertsource.pdf ' + filepath)
        os.unlink(filepath + '.convertsource.pdf')

        return returncode == 0


class PDFtoHTMLConverter(AbstractConverter):
    acceptforinput = [clam.common.formats.HTMLFormat]

    converttool = 'pdftohtml'

    def __init__(self, id,  **kwargs):
        super(PDFtoHTMLConverter,self).__init__(id, **kwargs)


    def convertforinput(self,filepath, metadata=None):
        super(PDFtoHTMLConverter,self).convertforinput(filepath, metadata)

        shutil.copy(filepath, filepath + '.convertsource.pdf')
        returncode = os.system(self.converttool + ' -layout ' + filepath + '.convertsource.pdf ' + filepath)
        os.unlink(filepath + '.convertsource.pdf')

        return returncode == 0


class MSWordConverter(AbstractConverter):
    acceptforinput = [clam.common.formats.PlainTextFormat]

    converttool = 'catdoc'

    def __init__(self, id,  **kwargs):
        super(MSWordConverter,self).__init__(id, **kwargs)


    def convertforinput(self,filepath, metadata=None):
        super(MSWordConverter,self).convertforinput(filepath, metadata)

        shutil.copy(filepath, filepath + '.convertsource.doc')
        returncode = os.system(self.converttool + ' -x ' + filepath + '.convertsource.doc > ' + filepath)
        os.unlink(filepath + '.convertsource.doc')

        return returncode == 0

