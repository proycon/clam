###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Job API  --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#
#       Centre for Language and Speech Technology / Language Machines
#       Radboud University Nijmegen
#
#       Licensed under GPLv3
#
###############################################################

#pylint: disable=wrong-import-order,bad-continuation

from __future__ import print_function, unicode_literals, division, absolute_import

import os
import io
import shutil
import flask #only used for rendering templates
import subprocess

import clam.common.util
import clam.common.data

DISPATCHER = 'clamdispatcher'

VERSION = '2.2'

class CLAMJob(object):
    NAME = None #overload
    VERSION = 0
    PROFILES = None
    PARAMETERS = None
    COMMAND = None
    SETTINGSMODULE = "NONE" #only needed for dispatching

    def __init__(self, projectpath, settingsmodule=None):
        self.id = self.__class__.__name__
        self.projectpath = projectpath
        if self.projectpath[-1] != '/':
            self.projectpath += '/'
        if not os.path.exists(self.projectpath):
            os.mkdir(self.projectpath)
        for d in ('input','output','tmp'):
            if not os.path.exists(d):
                os.mkdir(self.projectpath + '/' + d)

        self.errors = False
        self.parameters = []
        self.commandlineparams = []
        self.data = None
        self.nextseq = {}
        if settingsmodule:
            self.SETTINGSMODULE = settingsmodule
            import_string = "import " + settingsmodule + " as localsettings"
            exec(import_string) #pylint: disable=exec-used
            #load external configuration
            if hasattr(localsettings, 'PROFILES'): #pylint: disable=undefined-variable
                self.PROFILES = localsettings.PROFILES #pylint: disable=undefined-variable
            if hasattr(localsettings, 'PARAMETERS'): #pylint: disable=undefined-variable
                self.PARAMETERS = localsettings.PARAMETERS #pylint: disable=undefined-variable
            if hasattr(localsettings, 'COMMAND'): #pylint: disable=undefined-variable
                self.COMMAND = localsettings.COMMAND #pylint: disable=undefined-variable
            if hasattr(localsettings, 'SYSTEM_NAME'): #pylint: disable=undefined-variable
                self.NAME = localsettings.SYSTEM_NAME #pylint: disable=undefined-variable
            if hasattr(localsettings, 'SYSTEM_ID'): #pylint: disable=undefined-variable
                self.id = localsettings.SYSTEM_ID #pylint: disable=undefined-variable

    def addinputfile(self, sourcefile, **kwargs):
        filename = os.path.basename(sourcefile)
        if 'inputtemplate' in kwargs:
            inputtemplate_id = kwargs['inputtemplate']
            del kwargs['inputtemplate']
        inputtemplate = None
        for profile in self.PROFILES:
            for t in profile.input:
                if t.id == inputtemplate_id:
                    inputtemplate = t
        if not inputtemplate:
            #Check if the specified filename can be uniquely associated with an inputtemplate
            for profile in self.PROFILES:
                for t in profile.input:
                    if t.filename == filename:
                        if inputtemplate:
                            #we found another one, not unique!! reset and break
                            inputtemplate = None
                            break
                        else:
                            #good, we found one, don't break cause we want to make sure there is only one
                            inputtemplate = t
        if not inputtemplate:
            #Inputtemplate not found
            return Exception("Specified inputtemplate (" + inputtemplate_id + ") not found!")

        if inputtemplate.filename:
            filename = inputtemplate.filename

        #See if other previously uploaded input files use this inputtemplate
        if inputtemplate.unique:
            if inputtemplate.id in self.nextseq:
                raise Exception("You have already submitted a file of this type, you can only submit one. (Inputtemplate=" + inputtemplate.id + ", unique=True)")
            self.nextseq[inputtemplate.id]  = 0
        else:
            if inputtemplate.id in self.nextseq:
                self.nextseq[inputtemplate.id] += 1
            else:
                self.nextseq[inputtemplate.id] = 1

        #Make sure the filename is secure
        validfilename = True
        DISALLOWED = ('/','&','|','<','>',';','"',"'","`","{","}","\n","\r","\b","\t")
        for c in filename:
            if c in DISALLOWED:
                validfilename = False
                break

        if not validfilename:
            return ValueError("Filename contains invalid symbols! Do not use /,&,|,<,>,',`,\",{,} or ;")

        os.symlink(sourcefile, self.projectpath + '/input/' + filename)

        #Create a file object
        file = clam.common.data.CLAMInputFile(self.projectpath, filename, False) #get CLAMInputFile without metadata (chicken-egg problem, this does not read the actual file contents!

        #generate metadata
        errors, parameters = inputtemplate.validate(**kwargs)
        validmeta = True
        try:
            #Now we generate the actual metadata object (unsaved yet though). We pass our earlier validation results to prevent computing it again
            validmeta, metadata, parameters = inputtemplate.generate(file, (errors, parameters ))
            if validmeta:
                #And we tie it to the CLAMFile object
                file.metadata = metadata
                #Add inputtemplate ID to metadata
                metadata.inputtemplate = inputtemplate.id
            else:
                metadataerror = "Undefined error"
        except ValueError as msg:
            validmeta = False
            metadataerror = msg
        except KeyError as msg:
            validmeta = False
            metadataerror = msg

        if metadataerror:
            raise Exception('Metadata could not be generated, ' + str(metadataerror) + ',  this usually indicates an error in profile configuration')
        elif validmeta:
            #validate the file
            valid = file.validate()

            if valid:
                #Great! Everything ok, save metadata
                metadata.save(self.projectpath + 'input/' + file.metafilename())

                #And create symbolic link for inputtemplates
                linkfilename = os.path.dirname(filename)
                if linkfilename: linkfilename += '/'
                linkfilename += '.' + os.path.basename(filename) + '.INPUTTEMPLATE' + '.' + inputtemplate.id + '.' + str(self.nextseq[inputtemplate.id])
                os.symlink(self.projectpath + 'input/' + filename, self.projectpath + 'input/' + linkfilename)
            else:
                #Too bad, everything worked out but the file itself doesn't validate.
                #remove upload
                os.unlink(self.projectpath + 'input/' + filename)
                raise ValueError("File did not validate, it is not in the proper expected format")



    def __call__(self, **kwargs):
        self.errors,self.parameters, self.commandlineparams = clam.common.data.processparameters(kwargs, self.PARAMETERS)

        if not self.errors: #We don't even bother running the profiler if there are errors
            matchedprofiles, program = clam.common.data.profiler(self.PROFILES, self.projectpath, self.parameters, self.id, self.NAME if self.NAME else self.id, "")
            #converted matched profiles to a list of indices
            matchedprofiles_byindex = []
            for i, profile in enumerate(self.PROFILES):
                if profile in matchedprofiles:
                    matchedprofiles_byindex.append(i)

        if self.errors:
            #There are parameter errors, raise Exception
            for parameter in self.parameters:
                if parameter.error:
                    raise clam.common.data.ParameterError("Parameter " + parameter.id + " raised an error:" + parameter.error)
        elif not matchedprofiles:
            raise Exception("No profiles matching input and parameters, unable to start. Are you sure you added all necessary input files and set all necessary parameters?")
        else:
            clamdataxml = flask.render_template('response.xml',
                version=VERSION,
                system_id=self.__class__.__name__,
                system_name=self.NAME if self.NAME else self.__class__.__name__,
                system_description="",
                system_version=self.VERSION,
                system_email="",
                user="anonymous",
                project=os.path.basename(self.projectpath),
                url="",
                errors=self.errors,
                errormsg="",
                parameterdata=self.parameters,
                inputsources=None,
                outputpaths=[],
                inputpaths=clam.common.data.inputindex(self.projectpath, self.PROFILES),
                profiles=self.PROFILES,
                matchedprofiles=",".join([str(x) for x in matchedprofiles_byindex]), #comma-separated list of indices (str)
                program=program, #Program instance
                datafile=True,
                projects=[],
                actions=[],
                info=False
            )

            if self.COMMAND:
                #everything good, external call, serialize to XML file and dispatch external process
                with io.open(os.path.join(self.projectpath,"clam.xml"),'wb') as f:
                    f.write(clamdataxml)
                #dispatch process
                cmd = self.COMMAND
                cmd = cmd.replace('$PARAMETERS', " ".join(self.commandlineparams)) #commandlineparams is shell-safe
                cmd = cmd.replace('$INPUTDIRECTORY', self.projectpath + 'input/')
                cmd = cmd.replace('$OUTPUTDIRECTORY',self.projectpath + 'output/')
                cmd = cmd.replace('$TMPDIRECTORY',self.projectpath + 'tmp/')
                cmd = cmd.replace('$STATUSFILE',self.projectpath + '.status')
                cmd = cmd.replace('$DATAFILE',self.projectpath + 'clam.xml')
                cmd = cmd.replace('$USERNAME',"anonymous")
                cmd = cmd.replace('$PROJECT',os.path.basename(self.projectpath)) #alphanumeric only, shell-safe
                cmd = cmd.replace('$OAUTH_ACCESS_TOKEN','')
                cmd = clam.common.data.escapeshelloperators(cmd)
                #everything should be shell-safe now
                cmd += " 2> " + self.projectpath + "output/error.log" #add error output

                cmd = DISPATCHER + ' . ' + self.SETTINGSMODULE + ' ' + self.projectpath + ' ' + cmd
                #printlog("Starting dispatcher " +  DISPATCHER + " with " + self.COMMAND + ": " + repr(cmd) + " ..." )
                process = subprocess.Popen(cmd,cwd=self.projectpath, shell=True)
                if process:
                    pid = process.pid
                    #printlog("Started dispatcher with pid " + str(pid) )
                    with open(self.projectpath + '.pid','w') as f: #will be handled by dispatcher!
                        f.write(str(pid))
                    self.returncode = process.wait()
                    return self.returncode
                else:
                    raise Exception("Unable to launch process")
            else:
                #everything good, no external call, prepare data object
                return self.run(clam.common.data.CLAMData(clamdataxml))

    def run(self, data):
        """Called when the job has to run, should be overloaded, will be called when __call__ is invoked"""
        raise NotImplementedError("run() method should be overloaded")

    def clean(self):
        """Deletes all files for the job"""
        shutil.rmtree(self.projectpath)

