###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Metadata and profiling --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
##############################################################


import json
from lxml import etree as ElementTree

from clam.common.data import CLAMFile, CLAMInputFile
import clam.formats



def profiler(profiles, projectpath,parameters):
    """Given input files and parameters, produce metadata for outputfiles. Returns list of matched profiles if succesfull, empty list otherwise"""

    matched = []
    for profile in profiles:
        if profile.match(projectpath, parameters):
            matched.append(profile)
            profile.generate(projectpath,parameters)
    return matched


class Profile(object):
    def __init__(self, input, output, parameters): #, **kwargs):
        if not isinstance(input, list):
            input = [input]
        if isinstance(input, InputTemplate):
           assert all([ isinstance(InputTemplate) for x in input])
        self.input = input

        if isinstance(output, OutputTemplate) or isinstance(output, ParameterCondition):
            output = [output]
        assert all([ isinstance(OutputTemplate) or isinstance(ParameterCondition)  for x in output])
        self.output = output

        #Check for orphan OutputTemplates. OutputTemplates must have a parent (unless there is no input, then outputtemplates with filename, unique=True and copymetadata=False are parentless)
        for o in self.output:
            if isinstance(o, ParameterCondition):
                for o in o.allpossibilities():
                    parent = o._findparent(self.input)
                    if parent:
                        o.parent = parent
                        if not o.parent and (self.input or not o.unique or not o.filename):
                            raise Exception("Outputtemplate " + o.id + " has no parent defined, and none could be found automatically!")
            elif not o.parent:
                o.parent  = o._findparent(self.input)
                if not o.parent and (self.input or not o.unique or not o.filename):
                    raise Exception("Outputtemplate " + o.id + " has no parent defined, and none could be found automatically!")

    def match(self, projectpath, parameters):
        """Check if the profile matches all inputdata *and* produces output given the set parameters. Return boolean"""

        #check if profile matches inputdata (if there are no inputtemplate, this always matches intentionally!)
        for inputtemplate in self.input:
            if not inputtemplate.matchfiles(projectpath):
                return False
        
        #check if output is produced
        if not self.output: return False
        for outputtemplate in self.output:
            if isinstance(outputtemplate, ParameterCondition) and not outputtemplate.match(parameters):
                return False
        
        return True

    def matchingfiles(self, projectpath):
        """Return a list of all inputfiles matching the profile (filenames)"""
        l = []
        for inputtemplate in self.input:
            l += inputtemplate.matchfiles(projectpath)
        return l

    def generate(self, projectpath, parameters):
        """Generate output metadata on the basis of input files and parameters. Projectpath must be absolute."""
        
        
        if self.match(projectpath, parameters): #Does the profile match?
        
            #gather all input files that match
            inputfiles = self.matchingfiles(projectpath) #list of (seqnr, filename,inputtemplate) tuples
                                    
        
            for outputtemplate in self.output:
                if isinstance(outputtemplate, ParameterCondition) and outputtemplate.match(parameters):
                    outputtemplate = outputtemplate.evaluate(parameters)                
                #generate output files
                if outputtemplate:
                    if isinstance(outputtemplate, AbstractMetaField):                    
                        outputtemplate.generate(inputdir, parameters, projectpath, inputfiles)
                    else:
                        raise TypeError


    def xml(self):
        """Produce XML output for the profile""" #(independent of web.py for support in CLAM API)
        xml = "<profile"
        #if self.multi:
        #    xml += "  multi=\"yes\""
        #else:   
        #    xml += "  multi=\"no\""
        xml += ">\n<input>\n"
        for inputtemplate in self.input:
            xml += inputtemplate.xml()
        xml += "</input>\n"
        xml += "<output>\n"
        for outputtemplate in self.input:
            xml += outputtemplate.xml() #works for ParameterCondition as well!
        xml += "<output>\n"
        xml += "</profile>\n"
        return xml
        





class RawXMLProvenanceData(object):
    def __init__(self, xml):
        self.xml = xml
    
    def xml(self):
        if isinstance(self.xml, ElementTree._Element):
            return ElementTree.tostring(self.xml, pretty_print = True)
        else:
            return self.xml
    
class CLAMProvenanceData(object):
    
    def __init__(self, serviceid, servicename, serviceurl, outputtemplate_id, outputtemplate_label, inputfiles, parameters = None):
        self.serviceid = serviceid
        self.servicename = servicename
        self.serviceurl = serviceurl
        self.outputtemplate_id = outputtemplate_id
        self.outputtemplate_label = outputtemplate_label
        self.parameters = parameters    
            
        assert isinstance(inputfiles, list) and all([ isinstance(x,CLAMInputFile) for x in inputfiles ])
        self.inputfiles = inputfiles #list of CLAMMetaData objects of all input files
        
    def xml(self):
        xml += "<provenance type=\"clam\" id=\""+self.serviceid+"\" name=\"" +self.servicename+"\" url=\"" + self.serviceurl+"\" outputtemplate=\""+self.outputtemplate_id+"\" outputtemplatelabel=\""+self.outputtemplate_label+"\">"
        for inputfile in self.inputfiles:
            xml += "\t<inputfile name=\"" + inputfile.filename + "\">"
            xml += inputfile.metadata.xml()
            xml += "\t</inputfile>"            
            if self.parameters:
                xml += "<parameters>"
                for parameter in self.parameters:
                    xml += parameter.xml()
                xml += "</parameters>"
        xml += "</provenance>"
        return xml

class CLAMMetaData(object):
    """A simple hash structure to hold arbitrary metadata"""
    attributes = None #if None, all attributes are allowed! Otherwise it should be a dictionary with keys corresponding to the various attributes and a list of values corresponding to the *maximally* possible settings (include False as element if not setting the attribute is valid), if no list of values are defined, set True if the attrbute is required or False if not. If only one value is specified (either in a list or not), then it will be 'fixed' metadata

    mimetype = "" #No mimetype by default
    schema = ""
    
    self.provenance = None
    self.input = False
    self.output = False

    def __init__(self, file, **kwargs):
        assert isinstance(file, CLAMFile)
        self.data = {}
        self.loadinlinemetadata()
        for key, value in kwargs.items():
            if key == 'provenance':
                self.input = True
                assert (isinstance(value, CLAMProvenanceData))
                self.provenance = value
            else:
                self[key] = value
        if attributes:
            if not allowcustomattributes:
                for key, value in kwargs.items():
                    if not key in attributes:
                        raise KeyError("Invalid attribute '" + key + " specified. But this format does not allow custom attributes.")
                                        
            for key, valuerange in attributes.items():
                if isinstance(valuerange,list):
                    if not key in self and not False in valuerange :
                        raise ValueError("Required attribute " + key +  " not specified")
                    elif self[key] not in valuerange:
                        raise ValueError("Attribute assignment " + key +  "=" + self[key] + " has an invalid value, choose one of: " + " ".join(attributes[key])
                elif valuerange is False: #Any value is allowed, and this attribute is not required
                    pass #nothing to do
                elif valuerange is True: #Any value is allowed, this attribute is *required*    
                    if not key in self:
                        raise IncompleteError("Required attribute " + key +  " not specified")
                elif valuerange: #value is a single specific unconfigurable value 
                    self[key] = valuerange

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key)
        return key in self.data

    def items(self):
        return self.data.items()

    def __iter__(self):
        return self.data

    def __setitem__(self, key, value):
        if attributes != None and not key in attributes:
            raise KeyError
        assert not isinstance(value, list)
        maxvalues = self.data[key]
        if isinstance(maxvalues, list):
            if not value in maxvalues:
                raise ValueError
        self.data[key] = value


    def xml(self):
        """Render an XML representation of the metadata""" #(independent of web.py for support in CLAM API)
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += "<CLAMMetaData format=\"" + self.__class__.__name__ + "\"
        if self.mimetype:
             xml += " mimetype=\""+self.__class__.mimetype+"\""
        if self.schema:
             xml += " schema=\""+self.__class__.schema+"\""
        xml += ">\n"

        for key, value in self.data.items():
            xml += "\t<meta id=\""+key+"\">"+str(value)+"</meta>"

        if self.provenance:        
            xml += self.provenance.xml()
        
        xml += "</CLAMMetaData>"
        return xml

    def save(self, filename):
        f = codecs.open(filename,'w','utf-8')
        f.write(self.xml())
        f.close()
        
    def validate(self):
        #Should be overridden by subclasses
        return True
        
    def loadinlinemetadata(self):
        #Read inline metadata, can be overridden by subclasses
        pass
        
    def saveinlinemetadata(self):
        #Save inline metadata, can be overridden by subclasses
        pass
        
        

class CMDIMetaData(CLAMMetaData):
    #TODO LATER: implement



def profilefromxml():
    """Produce profile from xml"""
    raise NotImplementedError #TODO: implement
    

class InputTemplate(object):
    def __init__(self, id, formatclass, label, *args, **kwargs)
        assert (issubclass(formatclass, CLAMMetaData))
        assert (not '/' in id and not '.' in id)
        self.formatclass = formatclass
        self.id = id
        self.label = label

        self.parameters = []
        
        self.unique = True #may mark input/output as unique, even though profile may be in multi mode

        self.filename = None
        self.extension = None

        for key, value in kwargs.items():
            if key == 'unique':   
                self.unique = bool(value)
            elif key == 'multi':   
                self.unique = not bool(value)
            elif key == 'filename':
                self.filename = value # use '#' to insert a number in multi mode (will happen server-side!)
            elif key == 'extension':
                if value[0] == '.': #without dot
                    self.extension = value[1:]        
                else:
                    self.extension = value

        if not self.unique and not '#' in self.filename:
            raise Exception("InputTemplate configuration error, filename is set to a single specific name, but unique is disabled. Use '#' in filename, which will automatically resolve to a number in sequence.")

        for parameter in args:
            assert isinstance(parameter, AbstractParameter)
            self.parameters.append(parameter)


    def xml(self):
        """Produce Template XML"""
        xml = "<InputTemplate format=\"" + self.formatclass.__name__ + "\"" + " label=\"" + self.label + "\""
        if self.formatclass.mimetype:
            xml +=" mimetype=\""+self.formatclass.mimetype+"\""
        if self.formatclass.schema:
            xml +=" schema=\""+self.formatclass.schema+"\""
        if self.filename:
            xml +=" filename=\""+self.filename+"\""
        if self.extension:
            xml +=" extension=\""+self.extension+"\""
        if self.unique:
            xml +=" unique=\"yes\""
        xml += ">\n"
        for parameter in self.parameters:
            xml += parameter.xml()
        xml += "</InputTemplate>\n"
        return xml

            
    def json(self):
        """Produce a JSON representation for the web interface"""
        d = { 'id': self.id, 'format': self.formatclass.__name__,'label': self.label, 'mimetype': self.formatclass.mimetype,  'schema': self.formatclass.schema }
        if self.unique:
            d['unique'] = True
        if self.filename:
            d['filename'] = self.filename
        if self.extension:
            d['extension'] = self.extension
        #d['parameters'] = {}

        #The actual parameters are included as XML, and transformed by clam.js using XSLT (parameter.xsl) to generate the forms
        parametersxml = ''
        for parameter in self.parameters:
            #d['parameters'][parameter.id] = parameter.json()
            parameterxml = parameter.xml()
        d['parametersxml'] = parameterxml
        return json.dumps(d)

    def __eq__(self, other):
        return other.id == self.id

    def match(self, metadata, user = None):
        """Does the specified metadata match this template? returns (success,metadata,parameters)"""
        assert isinstance(metadata, self.formatclass)
        return self.generate(metadata,user)
        
    def matchingfiles(self, projectpath):
        """Checks if the input conditions are satisfied, i.e the required input files are present. We use the symbolic links .*.INPUTTEMPLATE.id.seqnr to determine this. Returns a list of matching results (seqnr, filename, inputtemplate)."""
        results = []
        
        if projectpath[-1] == '/':
             inputpath = projectpath + 'input/'
        else:
             inputpath = projectpath + '/input/'
             
        for linkf,realf in clam.common.util.globsymlinks(inputpath + '/.*.INPUTTEMPLATE.' + self.id + '.*'):
            seqnr = int(linkf.split('.')[-1])
            results.append( (seqnr, realf[len(inputpath):], self) )
        results = sorted(results)
        if self.unique and len(results) != 1: 
            return []
        else:
            return results

                
                
    def validate(self, inputdata, user = None):
        errors = False
        
        #we're going to modify parameter values, this we can't do
        #on the inputtemplate variable, that won't be thread-safe, we first
        #make a (shallow) copy and act on that          
        for parameter in self.parameters:
            parameters.append(copy(parameter))
        
        
        for parameter in parameters:
            if parameter.access(user):
                postvalue = parameter.valuefrompostdata(postdata) #parameter.id in postdata and postdata[parameter.id] != '':    
                if not (isinstance(postvalue,bool) and postvalue == False):
                    if parameter.set(postvalue): #may generate an error in parameter.error
                        params.append(parameter.compilearg(parameter.value))
                    else:
                        if not parameter.error: parameter.error = "Something mysterious went wrong whilst settings this parameter!" #shouldn't happen
                        printlog("Unable to set " + parameter.id + ": " + parameter.error)
                        errors = True
                elif parameter.required:
                    #Not all required parameters were filled!
                    parameter.error = "This option must be set"
                    errors = True
                if parameter.value and (parameter.forbid or parameter.require):
                    for parameter2 in parameters:
                            if parameter.forbid and parameter2.id in parameter.forbid and parameter2.value:
                                parameter.error = parameter2.error = "Setting parameter '" + parameter.name + "' together with '" + parameter2.name + "'  is forbidden"
                                printlog("Setting " + parameter.id + " and " + parameter2.id + "' together is forbidden")
                                errors = True
                            if parameter.require and parameter2.id in parameter.require and not parameter2.value:
                                parameter.error = parameter2.error = "Parameters '" + parameter.name + "' has to be set with '" + parameter2.name + "'  is"
                                printlog("Setting " + parameter.id + " requires you also set " + parameter2.id )
                                errors = True
        return errors, parameters


    def generate(self, file, inputdata, user = None, validatedata = None):
        """Convert the template into instantiated metadata, validating the data in the process and returning errors otherwise. inputdata is a dictionary-compatible structure, such as the relevant postdata. Return (success, metadata, parameters), error messages can be extracted from parameters[].error. Validatedata is a (errors,parameters) tuple that can be passed if you did validation in a prior stage, if not specified, it will be done automatically."""
        
        metadata = {}
        
        if not validatedata:
            errors,parameters = self.validate(inputdata,user)
        
        #scan errors and set metadata
        success = True
        for parameter in parameters:
            if parameter.error:
                success = False
            else:
                metadata[parameter.id] = parameter.value
 
        if not success:
            metadata = None
        else:
            try:
                metadata = self.formatclass(file, **metadata)
            except ValueError, KeyError:
                raise                
                
        return success, metadata, parameters
    
class AbstractMetaField(object): #for OutputTemplate only
    def __init__(self,key,value=None):
        self.key = key
        self.value = value

    def xml(self, operator='set'):
        xml += "\t<meta id=\"" + key + "\"";
        if operator != 'set':
            xml += " operator=\"" + operator + "\""
        if not value:
            xml += " />"
        else:
            xml += ">" + value + "</meta>" 
            
    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        #in most cases we're only interested in 'data'
        raise Exception("Always override this method in inherited classes! Return True if data is modified, False otherwise")

class SetMetaField(AbstractMetaField): 
    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        data[self.key] = value
        return True
        
class UnsetMetaField(AbstractMetaField):
    def xml(self):
        super(UnsetMetaField,self).xml('unset')
        
    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        if self.key in data and (not value or (value and data[self.key] == value)):
            del data[self.key]
            return True
        return False

class CopyMetaField(AbstractMetaField):
    """In CopyMetaField, the value is in the form of templateid.keyid, denoting where to copy from. If not keyid but only a templateid is
    specified, the keyid of the metafield itself will be assumed."""
    
    def xml(self):
        super(UnsetMetaField,self).xml('copy')
    
    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        raw = self.value.split('.')
        if len(raw) == 1:
            copytemplate = raw[0]
            copykey = self.key
        elif len(raw) == 2:
            copytemplate = raw[0]
            copykey = raw[1]
        else:
            raise Exception("Can't parse CopyMetaField value " + self.value)
        
        #find relevant inputfile
        edited = False
        for inputtemplate, f in relevantinputfiles:
            if inputtemplate.id == copytemplate:
                if copykey in f.metadata:
                    data[self.key] = f.metadata[copykey]                    
                    edited = True
        return edited
        
class OutputTemplate(object):
    def __init__(self, id, formatclass, label, *args, **kwargs)
        assert (issubclass(formatclass, CLAMMetaData))
        assert (not '/' in id and not '.' in id)
        self.id = id
        self.formatclass = formatclass
        self.label = label

        self.metafields = []
        for metafield in args:
            assert (isinstance(metafield, AbstractMetaField) or isinstance(metafield,ParameterCondition))
            self.metafields.append(metafield)
            
        
        self.unique = True #mark input/output as unique, as opposed to multiple files

        self.filename = None
        self.extension = None
        
        self.removeextensions = [] #Remove extensions
        
        self.parent = None #copy metadata from
        self.copymetadata = False #copy metadata from parent (if set)

        for key, value in kwargs.items():
            if key == 'unique':
                self.unique = bool(value)
            elif key == 'multi': #alias
                self.unique = not bool(value)
            elif key == 'filename':
                self.filename = value # use # to insert a number in multi mode
            elif key == 'removeextension':
                #remove the following extension(s) (prior to adding the extension specified)
                if value is True:
                    self.removeextensions = True #will remove all (only 1 level though)
                elif value is False:
                    pass
                elif not isinstance(value,list):
                    self.removeextensions = [value]
                else:
                    self.removeextensions = value
            elif key == 'extension':
                self.extension = value #Add the following extension
            elif key == 'parent':
                self.parent = value #The ID of an inputtemplate
            elif key == 'copymetadata':
                self.copymetadata = bool(value) #True by default
            elif key == 'viewers' or key == 'viewer':
                if isinstance(value, AbstractViewer):
                    self.viewers = [value]
                elif isinstance(value, list) and all([isinstance(x, AbstractViewer) for x in value]):
                    self.viewers = value
                else:
                    raise Exception("Invalid viewer specified!")


        if not self.unique and not '#' in self.filename:
            raise Exception("OutputTemplate configuration error, filename is set to a single specific name, but unique is disabled. Use '#' in filename, which will automatically resolve to a number in sequence.")

        

    def xml(self):
        """Produce Template XML"""
        xml = "<OutputTemplate format=\"" + self.formatclass.__name__ + "\"" + " label=\"" + self.label + "\""
        if self.formatclass.mimetype:
            xml +=" mimetype=\""+self.formatclass.mimetype+"\""
        if self.formatclass.schema:
            xml +=" schema=\""+self.formatclass.schema+"\""
        if self.unique:
            xml +=" unique=\"yes\""
        xml += ">\n"
        for metafield in self.metafields:
            xml += metafield.xml()
        xml += "</OutputTemplate>\n"
        return xml


    def __eq__(self, other):
        return other.id == self.id
    
    def _findparent(self, inputtemplates):
        """Find the most suitable parent, that is: the first matching unique/multi inputtemplate"""
        for inputtemplate in inputtemplates:
            if self.unique == inputtemplate.unique:
                return inputtemplate.id
        return None
                
    def _getparent(self, profile):
        """Resolve a parent ID"""
        assert (self.parent)
        for inputtemplate in profile.input:
            if inputtemplate == self.parent:
                return inputtemplate
        raise Exception("Parent InputTemplate '"+self.parent+"' not found!")

    def generatemetadata(self,filename, parameters, parentfile, relevantinputfiles):
        """Generate metadata, given a filename, parameters and a dictionary of inputdata (necessary in case we copy from it)"""
        data = {}
        
        if self.copymetadata:
            #Copy parent metadata  
            for key, value in parentfile.metadata.items():
                data[key] = value
        
        for metafield in self.metafields:
            if isinstance(metafield, ParameterCondition):
                metafield = metafield.evaluate(parameters)
                if not metafield:
                    continue
            assert(isinstance(metafield, AbstractMetaField))
            metafield.resolve(data, parameters, parentfile, relevantinputfiles)        
        return self.formatclass(filename, **data)


    def generate(self, profile, parameters, projectpath, inputfiles):
        """Yields (outputfilename, metadata) tuples"""
        
        #Get input files
        inputfiles = []
        parent = None
        if self.parent:
            #copy filename from parent
            parent = self._getparent(profile)
            
            #get input files for the parent InputTemplate
            parentinputfiles = parent.matchingfiles(projectpath)
            if not parentinputfiles:
                raise Exception("OutputTemplate '"+self.id + "' has parent '" + self.parent + "', but no matching input files were found!")
                
            #Do we specify a full filename?
            for seqnr, inputfilename, inputtemplate in parentinputfiles:
                if self.filename:
                    filename = self.filename
                elif parent:
                    filename = inputfilename
                    parentfile = CLAMInputFile(projectpath, inputfilename)
                else:
                    raise Exception("OutputTemplate '"+self.id + "' has no parent nor filename defined!")
            
                #Make actual CLAMInputFile objects of ALL relevant input files, that is: all unique=True files and all unique=False files with the same sequence number
                relevantinputfiles = []
                for seqnr2, inputfilename2, inputtemplate2 in inputfiles:
                    if seqnr2 == 0 or seqnr2 == seqnr:
                        relevantinputfiles.append( (inputtemplate2, CLAMInputFile(projectpath, inputfilename2)) )
                        
                #resolve # in filename
                if not self.unique:
                    filename.replace('#',str(seqnr))
            
                if self.removeextensions:
                    #Remove unwanted extensions
                    if removeextensions is True:
                        #Remove any extension
                        raw = filename.split('.')[:-1]
                        if raw:
                            filename = '.'.join(raw)
                    elif isinstance(removeextensions, list):
                        #Remove specified extension
                        for ext in self.removeextensions:  
                            if filename[-len(ext) - 1:] == '.' + ext:
                                filename = filename[:-len(ext) - 1]
                                    
                if self.extension and not self.filename:
                    filename += '.' + self.extension   
                    
                #Now we create the actual metadata
                yield filename, self.generatemetadata(self.filename, parameters, parentfile, relevantinputfiles)
                
        elif self.unique and self.filename:
            #outputtemplate has no parent, specified a filename and is unique, this implies it is not dependent on input files:

            yield filename, self.generatemetadata(self.filename, parameters, None, [])
            
        else:
            raise Exception("Unable to generate from OutputTemplate, no parent or filename specified")

                            
        
    
        
            
            
            


def ParameterCondition(object):
    def __init__(self, **kwargs):
        if not 'then' in kwargs:
            assert Exception("No 'then=' specified!")

        self.then = None
        self.otherwise = None

        self.conditions = []
        self.disjunction = False

        for key, value in kwargs.items():
            if key == 'then'
                if not isinstance(value, OutputTemplate) and not isinstance(value, InputTemplate) and not isinstance(value, ParameterCondition):
                    assert Exception("Value of 'then=' must be InputTemplate, OutputTemplate or ParameterCondition!")
                else:
                    self.then = value
            elif key == 'else' or key == 'otherwise':
                if not isinstance(value, OutputTemplate) and not isinstance(value, InputTemplate) and not isinstance(value, ParameterCondition):
                    assert Exception("Value of 'else=' must be InputTemplate, OutputTemplate or ParameterCondition!")
                else:
                    self.otherwise = value
            elif key == 'disjunction' or key == 'or':
                self.disjunction = value
            else:
                if key[-10:] == '_notequals':
                    self.conditions.append( (key[:-10], value,lambda x: x != value, 'notequals') )
                elif key[-12:] == '_greaterthan':
                    self.conditions.append( (key[:-12], value,lambda x: x > value, 'greaterthan') )
                elif key[-17:] == '_greaterequalthan':
                    self.conditions.append( (key[:-17],value, lambda x: x > value, 'greaterequalthan') )
                elif key[-9:] == '_lessthan':
                    self.conditions.append( (key[:-9],value, lambda x: x >= value , 'lessthan' ) )
                elif key[-14:] == '_lessequalthan':
                    self.conditions.append( (key[:-14], value,lambda x: x <= value, 'lessequalthan') )
                elif key[-9:] == '_contains':
                    self.conditions.append( (key[:-9], value,lambda x: x in value, 'contains') )
                elif key[-7:] == '_equals':
                    self.conditions.append( (key[:-7], value,lambda x: x == value, 'equals') )
                else: #default is _is
                    self.conditions.append( (key,value, lambda x: x == value,'equals') )
                    

    def match(self, parameters):
        for key,_,evalf,_ in self.conditions:
            if key in parameters:
                value = parameters[key]
            else:
                value = None
            if evalf(value):
                if self.disjunction:
                    return True
            else:
                if not self.disjunction: #conjunction
                    return False
         if self.disjunction:
             return False
         else:
             return True

    def allpossibilities(self):
        """Returns all possible outputtemplates that may occur (recusrively applied)"""
        l = []
        if isinstance(self.then, ParameterCondition):
            #recursive parametercondition
            l += self.then.allpossibilities()
        else:
            l.append(self.then)
        if self.otherwise:
            if isinstance(self.otherwise, ParameterCondition):
                l += self.otherwise.allpossibilities()
            else:
                l.append(self.otherwise)
        return l

    def evaluate(self, parameters):
        """Returns False if there's no match, or whatever the ParameterCondition evaluates to (recursively applied!)"""
        if self.match(parameters):
            if isinstance(self.then, ParameterCondition):
                #recursive parametercondition
                return self.then.evaluate()
            else:
                return self.then
        elif self.otherwise:
            if isinstance(self.otherwise, ParameterCondition):
                #recursive else
                return self.otherwise.evaluate()
            else:
                return self.otherwise
        return False

    def xml(self):
        xml = "<parametercondition>\n\t<if>\n"
        for key, value, evalf, operator in self.conditions:
            xml += "\t\t<" + operator + " parameter=\"" + key + "\">" + value + "</" + operator + ">"
        xml += "\t</if>\n\t<then>\n"
        xml += self.then.xml() #TODO LATER: add pretty indentation 
        xml += "\t</then>\n"
        if self.otherwise:
            xml += "\t<else>\n"
            xml += self.otherwise.xml() #TODO LATER: add pretty indentation 
            xml += "\t</else>"
        xml += "</parametercondition>"
        return xml








