#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Data API - Common data structures --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

from lxml import etree as ElementTree
from StringIO import StringIO
import urllib2
import httplib2
import os.path
import codecs
import json
import time
from copy import copy

import clam.common.parameters
import clam.common.status
import clam.common.util
import clam.common.viewers
#clam.common.formats is deliberately imported _at the end_ 

VERSION = '0.5'

class FormatError(Exception):
     """This Exception is raised when the CLAM response is not in the valid CLAM XML format"""
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return "Not a valid CLAM XML response"

class CLAMFile:
    basedir = ''
    
    def __init__(self, projectpath, filename, loadmetadata = True, user = None, password = None):
        """Create a CLAMFile object, providing immediate transparent access to CLAM Input and Output files, remote as well as local! And including metadata."""
        self.remote = (projectpath[0:7] == 'http://' or projectpath[0:8] == 'https://')
        self.projectpath = projectpath
        self.filename = filename
        self.metadata = None
        if loadmetadata:
            try:
                self.loadmetadata()
            except IOError:
                pass

        if self.remote:                
            self.http = httplib2.Http()
            if user and password:
                self.http.add_credentials(user, password)
                
        self.viewers = []
        self.converters = []
                
    def attachviewers(self, profiles):
        """Attach viewers *and converters* to file, automatically scan all profiles for outputtemplate or inputtemplate"""
        if self.metadata:
            template = None
            for profile in profiles:
                if isinstance(self, CLAMInputFile):
                    for t in profile.input:
                        if self.metadata.inputtemplate == t.id:
                            template = t
                            break
                elif isinstance(self, CLAMOutputFile) and self.metadata and self.metadata.provenance:
                    for t in profile.outputtemplates():
                        if self.metadata.provenance.outputtemplate_id == t.id:
                            template = t
                            break
                else:
                    raise NotImplementedError #Is ok, nothing to implement for now
                if template:
                    break
            if template and template.viewers:
                for viewer in template.viewers:
                    self.viewers.append(viewer)
            if template and template.converters:
                for converter in template.converters:
                    self.converters.append(converter)
                    
    def metafilename(self):
        """Returns the filename for the meta file (not full path). Only used for local files."""
        metafilename = os.path.dirname(self.filename) 
        if metafilename: metafilename += '/'
        metafilename += '.' + os.path.basename(self.filename) + '.METADATA'
        return metafilename
                
    def loadmetadata(self):
        """Load metadata for this file. This is usually called automatically upon instantiation, except if explicitly disabled."""
        if not self.remote:
            metafile = self.projectpath + self.basedir + '/' + self.metafilename()
            if os.path.exists(metafile):
                f = open(metafile, 'r')
                xml = "".join(f.readlines())
                f.close()
            else:
                raise IOError(2, "No metadata found!")
        else:
            try:
                response, xml = self.http.request(self.projectpath + self.basedir + '/' + self.filename + '/metadata')
            except:
                raise IOError(2, "Can't download metadata!")
            
            if response.status != 200: #TODO: Verify
                    raise IOError(2, "Can't download metadata from "+ self.projectpath + self.basedir + '/' + self.filename + '/metadata' + " , got HTTP response " + str(response.status) + "!")
        
        #parse metadata
        self.metadata = CLAMMetaData.fromxml(self, xml) #returns CLAMMetaData object (or child thereof)
     
    def __iter__(self):
        """Read the lines of the file, one by one. This only works for local files, remote files are loaded into memory first (a httplib2 limitation)."""
        if not self.remote:
            if self.metadata and 'encoding' in self.metadata:
                for line in codecs.open(self.projectpath + self.basedir + '/' + self.filename, 'r', self.metadata['encoding']).readlines():
                    yield line
            else:
                for line in open(self.projectpath + self.basedir + '/' + self.filename, 'r').readlines():
                    yield line
        else:
            for line in self.readlines():
                yield line
        
            #TODO LATER: Re-add streaming support with urllib2? (But mind the digest authentication!)
            #req = self.opener(self.projectpath + basedir '/' + self.filename) #urllib2
            #for line in req.readlines():
            #    yield line
            #req.close()
    
    def delete(self):
        """Delete this file"""
        if not self.remote:
            if not os.path.exists(self.projectpath + self.basedir + '/' + self.filename):
                return False
            else:
                os.unlink(self.projectpath + self.basedir + '/' + self.filename)
            
            #Remove metadata
            metafile = self.projectpath + self.basedir + '/' + self.metafilename()
            if os.path.exists(metafile):
                os.unlink(metafile)
            
            #also remove any .*.INPUTTEMPLATE.* links that pointed to this file: simply remove all dead links
            for linkf,realf in clam.common.util.globsymlinks(self.projectpath + self.basedir + '/.*.INPUTTEMPLATE.*'):
                    if not os.path.exists(realf):
                        os.unlink(linkf)
            
            return True
        else:
            httpcode, content = self.http.request(self.projectpath + self.basedir + '/' + self.filename,'DELETE')
            return True
         

    def readlines(self):
        """Loads all in memory"""
        if not self.remote:
            if self.metadata and 'encoding' in self.metadata:
               return codecs.open(self.projectpath + self.basedir + '/' + self.filename, 'r', self.metadata['encoding']).readlines()
            else:
               return open(self.projectpath + self.basedir + '/' + self.filename, 'r').readlines()
        else:
            httpcode, content = self.http.request(self.projectpath + self.basedir + '/' + self.filename)
            return content
        

    def validate(self):
        """Validate this file. Returns a boolean."""
        if self.metadata:
            return self.metadata.validate()
        else:
            return False


    def __str__(self):
        return self.projectpath + self.basedir + '/' + self.filename

class CLAMInputFile(CLAMFile):
    basedir = "input"
    
class CLAMOutputFile(CLAMFile):
    basedir = "output"

def getclamdata(filename):
    """This function reads the CLAM Data from an XML file. Use this to read
    the clam.xml file from your system wrapper. It returns a CLAMData instance."""
    f = open(filename,'r')
    xml = f.read(os.path.getsize(filename))
    f.close()
    return CLAMData(xml, True)
    
    
def processparameter(postdata, parameter, user=None):
    errors = False
    commandlineparam = ""
    
    if parameter.access(user):
        try:
            postvalue = parameter.valuefrompostdata(postdata)
        except:
            clam.common.util.printlog("Invalid value, unable to interpret parameter " + parameter.id + ", ...")
            parameter.error = "Invalid value, unable to interpret"
            return True, parameter, ''
        
        if not (postvalue is None):
            clam.common.util.printdebug("Setting parameter '" + parameter.id + "' to: " + repr(postvalue))
            if parameter.set(postvalue): #may generate an error in parameter.error                            
                p = parameter.compilearg()
                if p:
                    commandlineparam = p
            else:
                if not parameter.error: parameter.error = "Something undefined went wrong whilst setting this parameter!" #shouldn't happen
                clam.common.util.printlog("Unable to set " + parameter.id + ": " + parameter.error)
                errors = True
        elif parameter.required:
            #Not all required parameters were filled!
            parameter.error = "This parameter is mandatory and must be set!"
            errors = True

    return errors, parameter, commandlineparam
    
def processparameters(postdata, parameters, user=None):
        #we're going to modify parameter values, this we can't do
        #on the global variable, that won't be thread-safe, we first
        #make a (shallow) copy and act on that  
        
        commandlineparams = [] #for $PARAMETERS
        errors = False
        
        newparameters = [] #in same style as input (i.e. with or without groups)
        tempparlist = [] #always a list of parameters        
        
        if all([isinstance(x,tuple) for x in parameters ]):
            for parametergroup, parameterlist in parameters:
                newparameterlist = []
                for parameter in parameterlist:
                    error, parameter, commandlineparam = processparameter(postdata, copy(parameter), user)
                    errors = errors or error
                    newparameterlist.append(parameter)
                    tempparlist.append(parameter)
                    if commandlineparam:
                        commandlineparams.append(commandlineparam)                    
                newparameters.append( (parametergroup, newparameterlist) )
        elif all([isinstance(x,clam.common.parameters.AbstractParameter) for x in parameters]):
            for parameter in parameters:
                error, parameter, commandlineparam = processparameter(postdata, copy(parameter), user)
                errors = errors or error
                newparameters.append(copy(parameter))
                if commandlineparam:
                    commandlineparams.append(commandlineparam)                    
            tempparlist = newparameters
        else:
            raise Exception("Invalid parameters")
        
        #solve dependency issues now all values have been set:
        for parameter in tempparlist:    
            if parameter.hasvalue and (parameter.forbid or parameter.require):
                for parameter2 in tempparlist:
                    if parameter.forbid and parameter2.id in parameter.forbid and parameter2.hasvalue:
                        parameter.error = parameter2.error = "Setting parameter '" + parameter.name + "' together with '" + parameter2.name + "'  is forbidden"
                        clam.common.util.printlog("Setting " + parameter.id + " and " + parameter2.id + "' together is forbidden")
                        errors = True
                    if parameter.require and parameter2.id in parameter.require and not parameter2.hasvalue:
                        parameter.error = parameter2.error = "Parameter '" + parameter.name + "' has to be set with '" + parameter2.name + "'  is"
                        clam.common.util.printlog("Setting " + parameter.id + " requires you also set " + parameter2.id )
                        errors = True                     
                                                    
        return errors, newparameters, commandlineparams

class CLAMData(object): #TODO: Adapt CLAMData for new metadata
    """Instances of this class hold all the CLAM Data that is automatically extracted from CLAM
    XML responses. Its member variables are: 

        status          - Contains any of clam.common.status.*
        statusmessage   - The latest status message (string)
        completion      - An integer between 0 and 100 indicating
                          the percentage towards completion.
        parameters      - List of parameters (but use the methods instead)        
        profiles        - List of profiles ([ Profile ])
        input           - List of input files  ([ CLAMInputFile ])
        output          - List of output files ([ CLAMOutputFile ])
        projects        - List of projects ([ string ])
        corpora         - List of pre-installed corpora
        errors          - Boolean indicating whether there are errors in parameter specification
        errormsg        - String containing an error message

    Note that depending on the current status of the project, not all may be available.
    """

    def __init__(self, xml, localroot = False):
        """Pass an xml string containing the full response. It will be automatically parsed."""
        self.xml = xml
        
        self.system_id = ""
        self.system_name = ""
        
        #: String containing the base URL of the webserivice
        self.baseurl = ''
        
        #: String containing the full URL to the project, if a project was indeed selected
        self.projecturl = ''
        
        #: The current status of the service, returns clam.common.status.READY (1), clam.common.status.RUNNING (2), or clam.common.status.DONE (3)
        self.status = clam.common.status.READY
        
        #: The current status of the service in a human readable message
        self.statusmessage = ""
        self.completion = 0
        
        #: This contains a list of (parametergroup, [parameters]) tuples.
        self.parameters = []

        #: List of profiles ([ Profile ])    
        self.profiles = []
        
        #:  List of pre-installed corpora
        self.corpora = []
        
        #: List of output files ([ CLAMInputFile ])
        self.input = []
        
        #: List of output files ([ CLAMOutputFile ])
        self.output = []
        
        #: List of projects ([ string ])
        self.projects = None
        
        #: Boolean indicating whether there are errors in parameter specification
        self.errors = False        
        
        #: String containing an error message if an error occured
        self.errormsg = ""

        self.parseresponse(xml, localroot)
        


    def parseresponse(self, xml, localroot = False):
        """The parser, there's usually no need to call this directly"""
        global VERSION
        root = ElementTree.parse(StringIO(xml)).getroot()
        if root.tag != 'clam':
            raise FormatError()
            
        if root.attrib['version'][0:3] != VERSION[0:3]:
            raise Exception("Version mismatch, CLAM Data API has version " + VERSION + ", but response expects " + root.attrib['version'])                    
        self.system_id = root.attrib['id']
        self.system_name = root.attrib['name']        
        if 'project' in root.attrib:
            self.project = root.attrib['project']
        else:
            self.project = None
        if 'baseurl' in root.attrib:
            self.baseurl = root.attrib['baseurl']
            if self.project:
                if localroot == True: #implicit, assume CWD
                    self.remote = False
                    self.projecturl = '' #relative directory (assume CWD is project directory, as is the case when wrapper scripts are called)
                elif localroot: #explicit
                    self.remote = False 
                    self.projecturl = localroot + '/' + self.project + '/' #explicit directory
                else:
                    self.remote = True #no directory: remote URL
                    self.projecturl = self.baseurl + '/' + self.project + '/'



        if 'user' in root.attrib:
            self.user = root.attrib['user']
        else:
            self.user = None

        for node in root:
            if node.tag == 'status':
                self.status = int(node.attrib['code'])
                self.statusmessage  = node.attrib['message']
                self.completion  = node.attrib['completion']
                if 'errors' in node.attrib:
                    self.errors = ((node.attrib['errors'] == 'yes') or (node.attrib['errors'] == '1'))
                if 'errormsg' in node.attrib:
                    self.errormsg = node.attrib['errormsg']
            elif node.tag == 'parameters':
                for parametergroupnode in node:
                    if parametergroupnode.tag == 'parametergroup':
                        parameterlist = []
                        for parameternode in parametergroupnode:        
                            if parameternode.tag in vars(clam.common.parameters):
                                parameterlist.append(vars(clam.common.parameters)[parameternode.tag].fromxml(parameternode))
                            else:
                                raise Exception("Expected parameter class '" + parameternode.tag + "', but not defined!")
                        self.parameters.append( (parametergroupnode.attrib['name'], parameterlist) )
            elif node.tag == 'corpora':
                for corpusnode in node:
                    if corpusnode.tag == 'corpus':
                        self.corpora.append(corpusnode.value)
            elif node.tag == 'profiles':        
                for subnode in node:
                    if subnode.tag == 'profile':
                        self.profiles.append(Profile.fromxml(subnode))
            elif node.tag == 'input':
                 for filenode in node:
                     if filenode.tag == 'file':
                         for n in filenode:
                            if n.tag == 'name':
                                self.input.append( CLAMInputFile( self.projecturl, n.text ) )
            elif node.tag == 'output': 
                 for filenode in node:
                     if filenode.tag == 'file':
                        for n in filenode:
                            if n.tag == 'name':
                                self.output.append( CLAMOutputFile( self.projecturl, n.text ) )
            elif node.tag == 'projects':
                 self.projects = []
                 for projectnode in node:
                    if projectnode.tag == 'project':
                        self.projects.append(projectnode.text)

    def parameter(self, id):                                 
        """Return the specified global parameter"""
        for parametergroup, parameters in self.parameters:
            for parameter in parameters:
                if parameter.id == id:
                    return parameter
        raise KeyError("No such parameter exists: " + id )

    def __getitem__(self, id):                                 
        """Return the specified global parameter (alias for getparameter)"""
        try:
            return self.parameter(id)
        except KeyError:
            raise

    def __setitem__(self, id, value):
        """Set the specified parameter"""
        for parametergroup, parameters in self.parameters:
            for parameter in parameters:
                if parameter.id == id:
                    parameter.set(value)
                    return True
        raise KeyError
        
    def __contains__(self, id):
        """Check if a global parameter with the specified ID exists. Returns a boolean."""
        for parametergroup, parameters in self.parameters:
            for parameter in parameters:
                if parameter.id == id:
                    return True
        return False
        
    def parametererror(self):
        """Return the first parameter error, or False if there is none"""
        for parametergroup, parameters in self.parameters:
            for parameter in parameters:
                if parameter.error:
                    return parameter.error
        return false

    def passparameters(self):
        """Return all parameters as {id: value} dictionary"""
        paramdict = {}
        for parametergroup, params in self.parameters:
            for parameter in params:
                if parameter.value:
                    if isinstance(parameter.value, list):
                        paramdict[parameter.id] = ",".join(parameter.value)
                    else:
                        paramdict[parameter.id] = parameter.value
        return paramdict
        
        
    def inputtemplates(self):
        """Return all input templates as a list (of InputTemplate instances)"""
        l = []
        for profile in self.profiles:
            l += profile.input
        return l
        
    def inputtemplate(self,id):
        """Return the inputtemplate with the specified ID. This is used to resolve a inputtemplate ID to an InputTemplate object instance"""
        for profile in self.profiles:
            for inputtemplate in profile.input:
                if inputtemplate.id == id:
                    return inputtemplate            
        raise Exception("No such input template!")


def profiler(profiles, projectpath,parameters,serviceid,servicename,serviceurl):
    """Given input files and parameters, produce metadata for outputfiles. Returns list of matched profiles if succesfull, empty list otherwise"""

    matched = []
    for profile in profiles:
        if profile.match(projectpath, parameters):
            matched.append(profile)
            profile.generate(projectpath,parameters,serviceid,servicename,serviceurl)
    return matched



        
        

class Profile(object):
    def __init__(self, *args):
        """Create a Profile. Arguments can be of class InputTemplate, OutputTemplate or ParameterCondition"""
    
        self.input = []
        self.output = []
    
        for arg in args:
            if isinstance(arg, InputTemplate):    
                self.input.append(arg)
            elif isinstance(arg, OutputTemplate):    
                self.output.append(arg)
            elif isinstance(arg, ParameterCondition):
                self.output.append(arg)
                    
        #Check for orphan OutputTemplates. OutputTemplates must have a parent (only outputtemplates with filename, unique=True may be parentless)
        for o in self.output:
            if isinstance(o, ParameterCondition):
                for o in o.allpossibilities():
                    if not o:
                       continue 
                    if not isinstance(o, OutputTemplate):
                        raise Exception("ParameterConditions in profiles must always evaluate to OutputTemplate, not " + o.__class__.__name__ + "!")
                    parent = o._findparent(self.input)
                    if parent:
                        o.parent = parent
                        if not o.parent and (not (o.filename and o.unique)):
                            raise Exception("Outputtemplate '" + o.id + "' has no parent defined, and none could be found automatically!")
            elif not o.parent:
                    o.parent = o._findparent(self.input)
                    if not o.parent and (not (o.filename and o.unique)):
                        raise Exception("Outputtemplate '" + o.id + "' has no parent defined, and none could be found automatically!")

    def match(self, projectpath, parameters):
        """Check if the profile matches all inputdata *and* produces output given the set parameters. Return boolean"""
                        
        #check if profile matches inputdata (if there are no inputtemplate, this always matches intentionally!)
        for inputtemplate in self.input:
            if not inputtemplate.matchingfiles(projectpath):
                return False
        
        #check if output is produced
        outputproduced = False
        if not self.output: return False
        for outputtemplate in self.output:
            if not isinstance(outputtemplate, ParameterCondition) or outputtemplate.match(parameters):
                outputproduced = True
            
        return outputproduced

    def matchingfiles(self, projectpath):
        """Return a list of all inputfiles matching the profile (filenames)"""
        l = []
        for inputtemplate in self.input:
            l += inputtemplate.matchingfiles(projectpath)
        return l

    def outputtemplates(self):
        """Returns all outputtemplates, resolving ParameterConditions to all possibilities"""
        outputtemplates = []
        for o in self.output:
            if isinstance(o, ParameterCondition):
                outputtemplates += o.allpossibilities()
            else:
                assert isinstance(o, OutputTemplate)
                outputtemplates.append(o)
        return outputtemplates
            

    def generate(self, projectpath, parameters, serviceid, servicename,serviceurl):
        """Generate output metadata on the basis of input files and parameters. Projectpath must be absolute."""

        #Make dictionary of parameters
        d = {}
        for x in parameters:
            if isinstance(x,tuple) and len(x) == 2:
                for parameter in x[1]:  
                    d[parameter.id] = parameter
            elif isinstance(x, clam.common.parameters.AbstractParameter):
                d[x.id] = x
        parameters = d
                
        if self.match(projectpath, parameters): #Does the profile match?
        
            #gather all input files that match
            inputfiles = self.matchingfiles(projectpath) #list of (seqnr, filename,inputtemplate) tuples

            inputfiles_full = [] #We need the full CLAMInputFiles for generating provenance data
            for seqnr, filename, inputtemplate in inputfiles:
                inputfiles_full.append(CLAMInputFile(projectpath, filename))
                                        
            for outputtemplate in self.output:
                if isinstance(outputtemplate, ParameterCondition):
                    if outputtemplate.match(parameters):
                        outputtemplate = outputtemplate.evaluate(parameters)                
                    else:
                        continue
                #generate output files
                if outputtemplate:
                    #generate provenance data
                    provenancedata = CLAMProvenanceData(serviceid,servicename,serviceurl,outputtemplate.id, outputtemplate.label,  inputfiles_full, parameters)
                    
                    if isinstance(outputtemplate, OutputTemplate):                    
                        for outputfilename, metadata in outputtemplate.generate(self, parameters, projectpath, inputfiles, provenancedata):
                            clam.common.util.printdebug("Writing metadata for outputfile " + outputfilename)                            
                            metafilename = os.path.dirname(outputfilename) 
                            if metafilename: metafilename += '/'
                            metafilename += '.' + os.path.basename(outputfilename) + '.METADATA'                                                        
                            f = codecs.open(projectpath + '/output/' + metafilename,'w','utf-8')
                            f.write(metadata.xml())
                            f.close()
                    else:
                        raise TypeError("OutputTemplate expected, but got " + outputtemplate.__class__.__name__)


    def xml(self, indent = ""):
        """Produce XML output for the profile""" #(independent of web.py for support in CLAM API)
        xml = "\n" + indent + "<profile"
        xml += ">\n"
        xml += indent + " <input>\n"
        for inputtemplate in self.input:
            xml += inputtemplate.xml(indent +"\t") + "\n"
        xml += indent + " </input>\n"
        xml += indent + " <output>\n"
        for outputtemplate in self.output:
            xml += outputtemplate.xml(indent +"\t") + "\n" #works for ParameterCondition as well!
        xml += indent + " </output>\n"
        xml += indent + "</profile>"
        return xml
        
    def out(self, indent = ""):
        o = indent + "Profile" 
        o += indent + "\tInput"
        for inputtemplate in self.input:
            o += inputtemplate.out(indent +"\t") + "\n"            
        o += indent + "\tOutput"
        for outputtemplate in self.output:
            o += outputtemplate.out(indent +"\t") + "\n"

        return o
        
    @staticmethod
    def fromxml(node):
        """Return a profile instance from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element):
            node = ElementTree.parse(StringIO(node)).getroot() 
            
        args = []
            
        if node.tag == 'profile':
            for node in node:
                if node.tag == 'input':
                    for subnode in node:
                        if subnode.tag.lower() == 'inputtemplate':
                            args.append(InputTemplate.fromxml(subnode))
                elif node.tag == 'output':
                    for subnode in node:
                        if subnode.tag.lower() == 'outputtemplate':
                            args.append(OutputTemplate.fromxml(subnode))
                        elif subnode.tag.lower() == 'parametercondition':
                            args.append(ParameterCondition.fromxml(subnode))    
        return Profile(*args)
    



class RawXMLProvenanceData(object):
    def __init__(self, data):
        self.data = data
    
    def xml(self):
        if isinstance(self.data, ElementTree._Element):
            return ElementTree.tostring(self.data, pretty_print = True)
        else:
            return self.data
    
class CLAMProvenanceData(object):
    
    def __init__(self, serviceid, servicename, serviceurl, outputtemplate_id, outputtemplate_label, inputfiles, parameters = None, timestamp = None):
        self.serviceid = serviceid
        self.servicename = servicename
        self.serviceurl = serviceurl
        self.outputtemplate_id = outputtemplate_id
        self.outputtemplate_label = outputtemplate_label
        if parameters:
            if isinstance(parameters, dict):
                assert all([isinstance(x,clam.common.parameters.AbstractParameter) for x in parameters.values()])
                self.parameters = parameters    
            else:
                assert all([isinstance(x,clam.common.parameters.AbstractParameter) for x in parameters])
                self.parameters = parameters  
        else: 
            self.parameters = []
    
        if timestamp:
            self.timestamp = int(float(timestamp))
        else:
            self.timestamp = time.time()
            
        assert isinstance(inputfiles, list)
        if all([ isinstance(x,CLAMInputFile) for x in inputfiles ]):
            self.inputfiles = [ (x.filename, x.metadata) for x in inputfiles ] #list of (filename, CLAMMetaData) objects of all input files
        else:
            assert (all([ isinstance(x, tuple) and len(x) == 2 and isinstance(x[1], CLAMMetaData) for x in inputfiles ]))
            self.inputfiles = inputfiles
        
        
    def xml(self, indent = ""):
        xml = indent + "<provenance type=\"clam\" id=\""+self.serviceid+"\" name=\"" +self.servicename+"\" url=\"" + self.serviceurl+"\" outputtemplate=\""+self.outputtemplate_id+"\" outputtemplatelabel=\""+self.outputtemplate_label+"\" timestamp=\""+str(self.timestamp)+"\">"
        for filename, metadata in self.inputfiles:
            xml += indent + " <inputfile name=\"" + filename + "\">"
            xml += metadata.xml(indent + " ") + "\n"
            xml += indent +  " </inputfile>\n"            
        if self.parameters:
            xml += indent + " <parameters>\n"
            if isinstance(self.parameters, dict):
                parameters = self.parameters.values()
            elif isinstance(self.parameters, list):
                parameters = self.parameters
            for parameter in parameters: #TODO Later: make ordered?
                xml += parameter.xml(indent +"  ") + "\n"
            xml += indent + " </parameters>\n"
        xml += indent + "</provenance>"
        return xml

    @staticmethod
    def fromxml(node):
        """Return a CLAMProvenanceData instance from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element):
            node = ElementTree.parse(StringIO(node)).getroot() 
        if node.tag == 'provenance':
            if node.attrib['type'] == 'clam':
                serviceid = node.attrib['id']
                servicename = node.attrib['name']
                serviceurl = node.attrib['url']
                timestamp = node.attrib['timestamp']
                outputtemplate = node.attrib['outputtemplate']
                outputtemplatelabel = node.attrib['outputtemplatelabel']
                inputfiles = []
                parameters = []
                for subnode in node:
                    if subnode.tag == 'inputfile':
                        filename = node.attrib['name']
                        metadata = None
                        for subsubnode in subnode:
                            if subsubnode.tag == 'CLAMMetaData':
                                metadata = CLAMMetaData.fromxml(None, subsubnode)
                                break
                        inputfiles.append( (filename, metadata) )
                    elif subnode.tag == 'parameters':
                        for subsubnode in subnode:
                            if subsubnode.tag in vars(clam.common.parameters):
                                parameters.append(vars(clam.common.parameters)[subsubnode.tag].fromxml(subsubnode))
                            else:
                                raise Exception("Expected parameter class '" + subsubnode.tag + "', but not defined!")
                return CLAMProvenanceData(serviceid,servicename,serviceurl,outputtemplate, outputtemplatelabel, inputfiles, parameters, timestamp)
            else:
                raise NotImplementedError
            




class CLAMMetaData(object):
    """A simple hash structure to hold arbitrary metadata"""
    attributes = None #if None, all attributes are allowed! Otherwise it should be a dictionary with keys corresponding to the various attributes and a list of values corresponding to the *maximally* possible settings (include False as element if not setting the attribute is valid), if no list of values are defined, set True if the attrbute is required or False if not. If only one value is specified (either in a list or not), then it will be 'fixed' metadata
    allowcustomattributes = True

    mimetype = "" #No mimetype by default
    schema = ""
    

    def __init__(self, file, **kwargs):


        if isinstance(file, CLAMFile):
            self.file = file
        elif file is None:
            self.file = None
        else:
            raise Exception("Invalid file argument for CLAMMetaData")
            
            

        self.file = file #will be used for reading inline metadata, can be None if no file is associated        
        if self.file:
            self.file.metadata = self
        
        self.provenance = None

        self.inputtemplate = None

        self.data = {}
        self.loadinlinemetadata()
        for key, value in kwargs.items():
            if key == 'provenance':
                assert (isinstance(value, CLAMProvenanceData))
                self.provenance = value
            elif key == 'inputtemplate':
                if isinstance(value, InputTemplate):
                    self.inputtemplate = value.id
                else:
                    self.inputtemplate = value                    
            else:
                self[key] = value
        if self.attributes:
            if not self.allowcustomattributes:
                for key, value in kwargs.items():
                    if not key in self.attributes:
                        raise KeyError("Invalid attribute '" + key + " specified. But this format does not allow custom attributes. (format: " + self.__class__.__name__ + ", file: " + str(file) + ")")
                                        
            for key, valuerange in self.attributes.items():
                if isinstance(valuerange,list):
                    if not key in self and not False in valuerange :
                        raise ValueError("Required metadata attribute " + key +  " not specified")
                    elif self[key] not in valuerange:
                        raise ValueError("Attribute assignment " + key +  "=" + self[key] + " has an invalid value, choose one of: " + " ".join(self.attributes[key])) + " (format: " + self.__class__.__name__ + ", file: " + str(file) + ")"
                elif valuerange is False: #Any value is allowed, and this attribute is not required
                    pass #nothing to do
                elif valuerange is True: #Any value is allowed, this attribute is *required*    
                    if not key in self:
                        raise ValueError("Required metadata attribute " + key +  " not specified (format: " + self.__class__.__name__ + ", file: " + str(file) + ")" )
                elif valuerange: #value is a single specific unconfigurable value 
                    self[key] = valuerange

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data

    def items(self):
        return self.data.items()

    def __iter__(self):
        return self.data

    def __setitem__(self, key, value):
        if self.attributes != None and not key in self.attributes:
            if not self.allowcustomattributes:
                raise KeyError("Trying to set metadata field '" + key + "', but no custom attributes are allowed by the format")
        elif self.attributes and key in self.attributes:
            maxvalues = self.attributes[key]
            if isinstance(maxvalues, list):
                if not value in maxvalues:
                    raise ValueError("Invalid value '" + str(value) + "' for metadata field '" + key + "'")
            
        assert not isinstance(value, list)
        self.data[key] = value

    def xml(self, indent = ""):
        """Render an XML representation of the metadata""" #(independent of web.py for support in CLAM API)
        if not indent:
            xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        else:
            xml = ""
        xml += indent + "<CLAMMetaData format=\"" + self.__class__.__name__ + "\""
        if self.mimetype:
             xml += " mimetype=\""+self.mimetype+"\""
        if self.schema:
             xml += " schema=\""+self.schema+"\""
        if self.inputtemplate:
            xml += " inputtemplate=\""+self.inputtemplate+"\""
        xml += ">\n"

        for key, value in self.data.items():
            xml += indent + "  <meta id=\""+key+"\">"+str(value)+"</meta>\n"

        if self.provenance:        
            xml += self.provenance.xml(indent + "  ")
        
        xml += indent +  "</CLAMMetaData>"
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
    
    @staticmethod    
    def fromxml(file,node):
        """Read metadata from XML. Static method returning an CLAMMetaData instance (or rather; the appropriate subclass of CLAMMetaData) from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element):
            node = ElementTree.parse(StringIO(node)).getroot() 
        if node.tag == 'CLAMMetaData':
            format = node.attrib['format']
            
            formatclass = None
            if format in vars(clam.common.formats) and issubclass(vars(clam.common.formats)[format], CLAMMetaData):
                formatclass = vars(clam.common.formats)[format]
            if not formatclass:
                d = vars(clam.common.formats)
                raise Exception("Format class " + format + " not found!")
            
            data = {}    
            if 'inputtemplate' in node.attrib:
                data['inputtemplate'] = node.attrib['inputtemplate']
            if 'inputtemplatelabel' in node.attrib:
                data['inputtemplatelabel'] = node.attrib['inputtemplatelabel']

                
            
            for subnode in node:
                if subnode.tag == 'meta':
                    key = subnode.attrib['id']
                    value = subnode.text
                    data[key] = value
                elif subnode.tag == 'provenance':                
                    data['provenance'] = CLAMProvenanceData.fromxml(subnode)
            return formatclass(file, **data)
        else:    
            raise Exception("Invalid CLAM Metadata!")        

class CMDIMetaData(CLAMMetaData):
    #TODO LATER: implement
    pass




    
    


    

class InputTemplate(object):
    def __init__(self, id, formatclass, label, *args, **kwargs):
        assert (issubclass(formatclass, CLAMMetaData))
        assert (not '/' in id and not '.' in id)
        self.formatclass = formatclass
        self.id = id
        self.label = label

        self.parameters = []
        self.converters = []
        self.viewers = [] #TODO Later: Support viewers in InputTemplates?
        
        self.unique = True #may mark input/output as unique

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

        if not self.unique and (self.filename and not '#' in self.filename):
            raise Exception("InputTemplate configuration error for inputtemplate '" + self.id + "', filename is set to a single specific name, but unique is disabled. Use '#' in filename, which will automatically resolve to a number in sequence.")

        for arg in args:
            if isinstance(arg, clam.common.parameters.AbstractParameter):
                self.parameters.append(arg)
            elif isinstance(arg, clam.common.converters.AbstractConverter):
                self.converters.append(arg)
            elif isinstance(arg, clam.common.viewers.AbstractViewer):
                self.viewers.append(arg)
            else:
                raise ValueError("Unexpected parameter for InputTemplate " + id + ", expecting instance derived from AbstractParameter.")


    def xml(self, indent = ""):
        """Produce Template XML"""
        xml = indent + "<InputTemplate id=\""+self.id+"\" format=\"" + self.formatclass.__name__ + "\"" + " label=\"" + self.label + "\""
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
        else:
            xml +=" unique=\"no\""
        xml += ">\n"
        for parameter in self.parameters:
            xml += parameter.xml(indent+"\t") + "\n"
        if self.converters:
            for converter in self.converters:
                xml += indent + "\t<converter id=\""+converter.id+"\">"+converter.label+"</converter>"
        xml += indent + "</InputTemplate>"
        return xml

    @staticmethod
    def fromxml(node):
        """Static method returning an InputTemplate instance from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element):
            node = ElementTree.parse(StringIO(node)).getroot() 
        assert(node.tag.lower() == 'inputtemplate')
       
        id = node.attrib['id']
        format = node.attrib['format']
        label = node.attrib['label']
        kwargs = {}
        if 'filename' in node.attrib:
            kwargs['filename'] = node.attrib['filename']
        if 'extension' in node.attrib:
            kwargs['extension'] = node.attrib['extension']
        if 'unique' in node.attrib:
            if node.attrib['unique'].lower() == 'yes' or node.attrib['unique'].lower() == 'true' or node.attrib['unique'].lower() == '1':
                kwargs['unique'] = True
            else:
                kwargs['unique'] = False
            
        #find formatclass
        if format in vars(clam.common.formats):
            formatcls = vars(clam.common.formats)[format]
        else:
            raise Exception("Expected format class '" + format+ "', but not defined!")

        args = []
        for subnode in node:
            if subnode.tag in vars(clam.common.parameters):
                args.append(vars(clam.common.parameters)[subnode.tag].fromxml(subnode))
            elif subnode.tag == 'converter':
                pass #TODO: Reading converters from XML is not implemented (and not necessary at this stage)
            elif subnode.tag == 'viewer':
                pass #TODO: Reading viewers from XML is not implemented (and not necessary at this stage)
            else:
                raise Exception("Expected parameter class '" + subnode.tag + "', but not defined!")
                            
        return InputTemplate(id,formatcls,label, *args, **kwargs)     


            
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
            parametersxml += parameter.xml()
        d['parametersxml'] = '<?xml version="1.0" encoding="utf-8" ?><parameters>' + parametersxml + '</parameters>'
        d['converters'] = [ {'id':x.id, 'label':x.label} for x in self.converters ]
        return json.dumps(d)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.id == other
        else: #object
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

                
                
    def validate(self, postdata, user = None):            
        clam.common.util.printdebug("Validating inputtemplate " + self.id + "...")
        errors, parameters, _  = processparameters(postdata, self.parameters, user)        
        return errors, parameters
        



    def generate(self, file, validatedata = None,  inputdata=None, user = None):
        """Convert the template into instantiated metadata, validating the data in the process and returning errors otherwise. inputdata is a dictionary-compatible structure, such as the relevant postdata. Return (success, metadata, parameters), error messages can be extracted from parameters[].error. Validatedata is a (errors,parameters) tuple that can be passed if you did validation in a prior stage, if not specified, it will be done automatically."""
        
        metadata = {}
        
        if not validatedata:
            assert inputdata
            errors,parameters = self.validate(inputdata,user)
        else:
            errors, parameters = validatedata
                
        #scan errors and set metadata
        success = True
        for parameter in parameters:
            assert isinstance(parameter, clam.common.parameters.AbstractParameter)
            if parameter.error:
                success = False
            else:
                metadata[parameter.id] = parameter.value
 
        if not success:
            metadata = None
        else:
            try:
                metadata = self.formatclass(file, **metadata)
            except:
                raise                
                
        return success, metadata, parameters
    
class AbstractMetaField(object): #for OutputTemplate only
    def __init__(self,key,value=None):
        self.key = key
        self.value = value

    def xml(self, operator='set', indent = ""):
        xml = indent + "<meta id=\"" + self.key + "\"";
        if operator != 'set':
            xml += " operator=\"" + operator + "\""
        if not self.value:
            xml += " />"
        else:
            xml += ">" + self.value + "</meta>" 
        return xml

    @staticmethod
    def fromxml(node):
        """Static method returning an MetaField instance (any subclass of AbstractMetaField) from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element):
            node = ElementTree.parse(StringIO(node)).getroot() 
        if node.tag.lower() != 'meta':
            raise Exception("Expected meta tag but got '" + node.tag + "' instead")
       
        key = node.attrib['id']        
        if node.text:
            value = node.text
        else:
            value = None
        operator = 'set'
        if 'operator' in node.attrib:
            operator= node.attrib['operator']
        if operator == 'set':
            cls = SetMetaField
        elif operator == 'unset':
            cls = UnsetMetaField
        elif operator == 'copy':
            cls = CopyMetaField
        elif operator == 'parameter':
            cls = ParameterMetaField
        return cls(key, value)
        
            
    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        #in most cases we're only interested in 'data'
        raise Exception("Always override this method in inherited classes! Return True if data is modified, False otherwise")
    

class SetMetaField(AbstractMetaField): 
    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        data[self.key] = self.value
        return True
        
    def xml(self, indent=""):
        return super(SetMetaField,self).xml('set', indent)
        
class UnsetMetaField(AbstractMetaField):
    def xml(self, indent = ""):
        return super(UnsetMetaField,self).xml('unset', indent)
        
    def resolve(self, data, parameters, parentfile, relevantinputfiles):
        if self.key in data and (not self.value or (self.value and data[self.key] == self.value)):
            del data[self.key]
            return True
        return False

class CopyMetaField(AbstractMetaField):
    """In CopyMetaField, the value is in the form of templateid.keyid, denoting where to copy from. If not keyid but only a templateid is
    specified, the keyid of the metafield itself will be assumed."""
    
    def xml(self, indent = ""):
        return super(CopyMetaField,self).xml('copy', indent)
    
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
                if f.metadata and copykey in f.metadata:
                    data[self.key] = f.metadata[copykey]                    
                    edited = True
        return edited
        
class ParameterMetaField(AbstractMetaField):
    def xml(self, indent=""):
        return super(ParameterMetaField,self).xml('parameter', indent)
    
    def resolve(self, data, parameters, parentfile, relevantinputfiles): #TODO: Verify
        if self.value in parameters:
            data[self.key] = parameters[self.value]
            return True
        else:
            return False
        
class OutputTemplate(object):
    def __init__(self, id, formatclass, label, *args, **kwargs):
        assert (issubclass(formatclass, CLAMMetaData))
        assert (not '/' in id and not '.' in id)
        self.id = id
        self.formatclass = formatclass
        self.label = label

        self.viewers = []
        self.converters = []

        self.metafields = []
        for arg in args:
            if isinstance(arg, AbstractMetaField) or isinstance(arg,ParameterCondition):
                self.metafields.append(arg)
            elif isinstance(arg, clam.common.converters.AbstractConverter):
                self.converters.append(arg)
            elif isinstance(arg, clam.common.viewers.AbstractViewer):
                self.viewers.append(arg)
            else:
                raise ValueError("Unexpected argument for OutputTemplate " + id + ", expecting MetaField, ParameterCondition, Viewer or Converter")
            
        
        self.unique = True #mark input/output as unique, as opposed to multiple files

        self.filename = None
        self.extension = None
        
        self.removeextensions = [] #Remove extensions
        
        self.parent = None
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
                if value[0] == '.':
                    self.extension = value[1:]
                else:
                    self.extension = value #Add the following extension
            elif key == 'parent':
                if isinstance(value, InputTemplate): value = value.id
                self.parent = value #The ID of an inputtemplate
            elif key == 'copymetadata':
                self.copymetadata = bool(value) #True by default
            elif key == 'viewers' or key == 'viewer':
                if isinstance(value, clam.common.viewers.AbstractViewer):
                    self.viewers = [value]
                elif isinstance(value, list) and all([isinstance(x, clam.common.viewers.AbstractViewer) for x in value]):
                    self.viewers = value
                else:
                    raise Exception("Invalid viewer specified!")


        if not self.unique and (self.filename and not '#' in self.filename):
            raise Exception("OutputTemplate configuration error in outputtemplate '" + self.id + "', filename is set to a single specific name, but unique is disabled. Use '#' in filename, which will automatically resolve to a number in sequence.")


    def xml(self, indent = ""):
        """Produce Template XML"""
        xml = indent + "<OutputTemplate id=\"" + self.id + "\" format=\"" + self.formatclass.__name__ + "\"" + " label=\"" + self.label + "\""
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
        else:
            xml +=" unique=\"no\""
        xml += ">\n"
        for metafield in self.metafields:
            xml += metafield.xml(indent + "\t") + "\n"

        xml += indent + "</OutputTemplate>"
        return xml
    
    @staticmethod    
    def fromxml(node):
        """Static method return an OutputTemplate instance from the given XML description. Node can be a string or an etree._Element."""
        if not isinstance(node,ElementTree._Element):
            node = ElementTree.parse(StringIO(node)).getroot() 
        assert(node.tag.lower() == 'outputtemplate')
        
        id = node.attrib['id']
        format = node.attrib['format']
        label = node.attrib['label']
        kwargs = {}
        if 'filename' in node.attrib:
            kwargs['filename'] = node.attrib['filename']
        if 'extension' in node.attrib:
            kwargs['extension'] = node.attrib['extension']
        if 'unique' in node.attrib:
            if node.attrib['unique'].lower() == 'yes' or node.attrib['unique'].lower() == 'true' or node.attrib['unique'].lower() == '1':
                kwargs['unique'] = True
            else:
                kwargs['unique'] = False
            
        #find formatclass
        if format in vars(clam.common.formats):
            formatcls = vars(clam.common.formats)[format]
        else:
            raise Exception("Specified format not defined!")

        args = []
        for subnode in node:
            if subnode.tag == 'parametercondition':
                args.append(ParameterCondition.fromxml(subnode))
            elif subnode.tag == 'converter':
                pass #TODO: Reading converters from XML is not implemented (and not necessary at this stage)
            elif subnode.tag == 'viewer':
                pass #TODO: Reading viewers from XML is not implemented (and not necessary at this stage)                
            else:            
                args.append(AbstractMetaField.fromxml(subnode))        
            
        return OutputTemplate(id,formatcls,label, *args, **kwargs)     


            
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

    def generate(self, profile, parameters, projectpath, inputfiles, provenancedata=None): 
        """Yields (outputfilename, metadata) tuples"""
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
                    if self.removeextensions is True:
                        #Remove any extension
                        raw = filename.split('.')[:-1]
                        if raw:
                            filename = '.'.join(raw)
                    elif isinstance(self.removeextensions, list):
                        #Remove specified extension
                        for ext in self.removeextensions:  
                            if filename[-len(ext) - 1:] == '.' + ext:
                                filename = filename[:-len(ext) - 1]
                                    
                if self.extension and not self.filename:
                    filename += '.' + self.extension   
                    
                #Now we create the actual metadata
                yield filename, self.generatemetadata(parameters, parentfile, relevantinputfiles, provenancedata)
                
        elif self.unique and self.filename:
            #outputtemplate has no parent, but specified a filename and is unique, this implies it is not dependent on input files:

            yield self.filename, self.generatemetadata(parameters, None, [], provenancedata)
            
        else:
            raise Exception("Unable to generate from OutputTemplate, no parent or filename specified")


    def generatemetadata(self, parameters, parentfile, relevantinputfiles, provenancedata = None):
        """Generate metadata, given a filename, parameters and a dictionary of inputdata (necessary in case we copy from it)"""
        assert isinstance(provenancedata,CLAMProvenanceData) or provenancedata == None

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

        if provenancedata:
            data['provenance'] = provenancedata

        return self.formatclass(None, **data)






class ParameterCondition(object):
    def __init__(self, **kwargs):
        if not 'then' in kwargs:
            raise Exception("No 'then=' specified!")

        self.then = None
        self.otherwise = None

        self.conditions = []
        self.disjunction = False

        for key, value in kwargs.items():
            if key == 'then':
                if isinstance(value, OutputTemplate) or isinstance(value, InputTemplate) or isinstance(value, ParameterCondition) or isinstance(value, AbstractMetaField):
                    self.then = value
                else:
                    raise Exception("Value of 'then=' must be InputTemplate, OutputTemplate or ParameterCondition!")                    
            elif key == 'else' or key == 'otherwise':
                if isinstance(value, OutputTemplate) or isinstance(value, InputTemplate) or isinstance(value, ParameterCondition) or isinstance(value, AbstractMetaField):
                    self.otherwise = value                    
                else:
                    raise Exception("Value of 'else=' must be InputTemplate, OutputTemplate or ParameterCondition!")
                    
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
                elif key[-4:] == '_set':
                    if value:
                        self.conditions.append( (key[:-4], value,lambda x: x, 'set') )
                    else:
                        self.conditions.append( (key[:-4], value,lambda x: not x, 'set') )
                else: #default is _equals
                    self.conditions.append( (key,value, lambda x: x == value,'equals') )

        if self.then is None:
            raise Exception("No then= specified for ParameterCondition!")

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
        elif self.then:
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

    def xml(self, indent = ""):
        xml = indent + "<parametercondition>\n" + indent + " <if>\n"
        for key, value, evalf, operator in self.conditions:
            xml += indent + "  <" + operator + " parameter=\"" + key + "\">" + str(value) + "</" + operator + ">\n"
        xml += indent + " </if>\n" + indent + " <then>\n"
        xml += self.then.xml(indent + "\t") + "\n"
        xml += indent + " </then>\n"
        if self.otherwise:
            xml += indent + " <else>\n"
            xml += self.otherwise.xml(indent + " \t") + "\n"
            xml += indent + " </else>"
        xml += indent + "</parametercondition>"
        return xml

    @staticmethod
    def fromxml(node):    
        """Static method returning a ParameterCondition instance from the given XML description. Node can be a string or an etree._Element."""    
        if not isinstance(node,ElementTree._Element):
            node = ElementTree.parse(StringIO(node)).getroot() 
        assert(node.tag.lower() == 'parametercondition')
        
        kwargs = {}
        
        found = False
        for node in node:
            if node.tag == 'if':
                #interpret conditions:
                for subnode in node:
                    operator = subnode.tag
                    parameter = subnode.attrib['parameter']
                    value = subnode.text
                    kwargs[parameter + '_' + operator] = value
                    found = True
            elif node.tag == 'then' or node.tag == 'else' or node.tag == 'otherwise':
                #interpret statements:        
                for subnode in node: #TODO LATER: Support for multiple statement in then=, else= ?
                    if subnode.tag.lower() == 'parametercondition':
                        kwargs[node.tag] = ParameterCondition.fromxml(subnode)
                    elif subnode.tag == 'meta':                
                        #assume metafield?
                        kwargs[node.tag] = AbstractMetaField.fromxml(subnode)                
                    elif subnode.tag.lower() == 'outputtemplate':
                        kwargs[node.tag] = OutputTemplate.fromxml(subnode) 
        if not found:
            raise Exception("No condition found in ParameterCondition!")
        return ParameterCondition(**kwargs)










import clam.common.formats #yes, this is deliberately placed at the end!
