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


import shutil
import io
import os
import flask
from clam.common.data import CLAMMetaData, CLAMOutputFile, AbstractConverter
from clam.common.util import withheaders
import clam.common.formats


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

