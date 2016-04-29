###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Data API  --
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
import clam.common.util
import clam.common.data
import flask #only used for rendering templates

DISPATCHER = 'clamdispatcher'

VERSION = '2.2'

class CLAMJob(object):
    NAME = None #overload
    VERSION = 0
    PROFILES = None
    PARAMETERS = None
    COMMAND = None
    SETTINGSMODULE = 'clam.config.dispatcheronly' #only needed for dispatching

    def __init__(self, projectpath, settingsmodule=None, async=False):
        self.id = self.__class__.__name__
        self.projectpath = projectpath
        if self.projectpath[-1] != '/':
            self.projectpath += '/'
        self.errors = False
        self.parameters = []
        self.commandlineparams = []
        self.data = None
        self.async = async
        self.oncompletion = oncompletion
        if settingsmodule:
            self.SETTINGSMODULE = settingsmodule
            import_string = "import " + settingsmodule + " as localsettings"
            exec(import_string) #pylint: disable=exec-used
            #load external configuration
            if hasattr(localsettings, 'PROFILES'):
                self.PROFILES = localsettings.PROFILES
            if hasattr(localsettings, 'PARAMETERS'):
                self.PARAMETERS = localsettings.PARAMETERS
            if hasattr(localsettings, 'COMMAND'):
                self.COMMAND = localsettings.COMMAND
            if hasattr(localsettings, 'SYSTEM_NAME'):
                self.NAME = localsettings.SYSTEM_NAME
            if hasattr(localsettings, 'SYSTEM_ID'):
                self.id = localsettings.SYSTEM_ID

    def start(self, **kwargs):
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
        elif self.COMMAND:
            #everything good, external call, serialize to XML file and dispatch external process
            with io.open(os.path.join(self.projectpath,"clam.xml"),'wb') as f:
                f.write(flask.render_template('response.xml',
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
                    ))
            #dispatch process
            cmd = self.COMMAND
            cmd = cmd.replace('$PARAMETERS', " ".join(self.commandlineparams)) #commandlineparams is shell-safe
            cmd = cmd.replace('$INPUTDIRECTORY', self.projectpath + 'input/')
            cmd = cmd.replace('$OUTPUTDIRECTORY',self.projectpath + 'output/')
            cmd = cmd.replace('$TMPDIRECTORY',self.projectpath + 'tmp/')
            cmd = cmd.replace('$STATUSFILE',self.projectpath + '.status')
            cmd = cmd.replace('$DATAFILE',self.projectpath + 'clam.xml')
            cmd = cmd.replace('$USERNAME',"anonymous")
            cmd = cmd.replace('$PROJECT',os.path.basename(self.projectpath)) #alphanumberic only, shell-safe
            cmd = cmd.replace('$OAUTH_ACCESS_TOKEN','')
            cmd = clam.common.data.escapeshelloperators(cmd)
            #everything should be shell-safe now
            cmd += " 2> " + self.projectpath + "output/error.log" #add error output

            cmd = DISPATCHER + ' . ' + self.SETTINGSMODULE + ' ' + self.projectpath + ' ' + cmd
            printlog("Starting dispatcher " +  DISPATCHER + " with " + self.COMMAND + ": " + repr(cmd) + " ..." )
            process = subprocess.Popen(cmd,cwd=self.projectpath, shell=True)
            if process:
                pid = process.pid
                printlog("Started dispatcher with pid " + str(pid) )
                with open(self.projectpath + '.pid','w') as f: #will be handled by dispatcher!
                    f.write(str(pid))
                if not self.async:
                    self.returncode = process.wait()
                    return self.returncode
                else:
                    return None
            else:
                raise Exception("Unable to launch process")
        else:
            #everything good, no external call, prepare data object
            self.run(data)

        self.done()


    def __call__(self): #alias
        self.start()

    def done(self):
        pass

    def run(self, data):
        raise NotImplementedError("run() method should be overloaded")

