#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Wrapper script Template --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#       Centre for Language and Speech Technology
#       Radboud University Nijmegen
#
#       (adapt or remove this header for your own code)
#
#       Licensed under GPLv3
#
###############################################################

#This is a template wrapper which you can use a basis for writing your own
#system wrapper script. The system wrapper script is called by CLAM, it's job it
#to call your actual tool.

#This script will be called by CLAM and will run with the current working directory set to the specified project directory

#This wrapper script uses Python and the CLAM Data API.
#We make use of the XML settings file that CLAM outputs, rather than
#passing all parameters on the command line.


#import some general python modules:
import sys

#import CLAM-specific modules. The CLAM API makes a lot of stuff easily accessible.
import clam.common.data
import clam.common.status

#When the wrapper is started, the current working directory corresponds to the project directory, input files are in input/ , output files should go in output/ .

#make a shortcut to the shellsafe() function
shellsafe = clam.common.data.shellsafe

#this script takes three arguments from CLAM: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY
#(as configured at COMMAND= in the service configuration file, there you can
#reconfigure which arguments are passed and in what order.
datafile = sys.argv[1]
statusfile = sys.argv[2]
outputdir = sys.argv[3]

#If you make use of CUSTOM_FORMATS, you need to import your service configuration file here and set clam.common.data.CUSTOM_FORMATS
#Moreover, you can import any other settings from your service configuration file as well:

#from yourserviceconf import CUSTOM_FORMATS
#clam.common.data.CUSTOM_FORMATS = CUSTOM_FORMATS

#Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml)), always pass CUSTOM_FORMATS as second argument if you make use of it!
clamdata = clam.common.data.getclamdata(datafile)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

clam.common.status.write(statusfile, "Starting...")


#=========================================================================================================================

# Below are some examples of how to access the input files and expected output
# files. Choose and adapt one of examples A, B or C.

#-- EXAMPLE A: Iterate over the program --

# The 'program' describes exactly what output files will/should be generated on the
# basis of what input files. It is the concretisation of the profiles and is the
# most elegant method to set up your wrapper.

#for outputfile, outputtemplate_id in clamdata.program.getoutputfiles():
#   if outputtemplate_id == 'some_template_id':
        #(Use outputtemplate_id to match against output templates)
        #(You can access output metadata using outputfile.metadata[parameter_id])
#       outputfilepath = str(outputfile) #example showing how to obtain the path to the file
        #if you expect just a single input file for this output file, you can use this:
#       inputfile, inputtemplate = clamdata.program.getinputfile(outputfilepath)
        # ...do your thing... e.g., invoke a process that generates outputfilename on the basis of inputfilename (see the invoke your actual system example below)
        #(You can access input metadata using inputfile.metadata[parameter_id])

        #if, on the other hand, you expect multiple input files, then you can iterate over them:
#       for inputfile, inputtemplate_id in clamdata.program.getinputfiles(outputfilename):
#           if inputtemplate_id == 'some_input_template_id':
#           inputfilepath = str(inputfile) #example showing how to obtain the path to the file
            #...
        #...do your thing... e.g., invoke a process that generates outputfilename on the basis all inputfilenames

#-- EXAMPLE B: Iterate over all input files? --

# This example iterates over all input files, it can be a simpler
# method for setting up your wrapper:

#for inputfile in clamdata.input:
#   inputtemplate = inputfile.metadata.inputtemplate
#   inputfilepath = str(inputfile)
#   encoding = inputfile.metadata['encoding'] #Example showing how to obtain metadata parameters

#(Note: Both these iteration examples will fail if you change the current working directory, so make sure to set it back to the initial path if you do need to change it!!)

#-- EXAMPLE C: Grab a specific input file? (by input template) --

# Iteration over all input files is often not necessary either, you can just do:

#inputfile = clamdata.inputfile('replace-with-inputtemplate-id')
#inputfilepath = str(inputfile)

#========================================================================================

# Below is an example of how to read global parameters and how to invoke your
# actual system. You may want to integrete these into one of the solution
# examples A,B or C above.

#-- Read global parameters? --

# Global parameters are accessed by addressing the clamdata instance as-if were a simple dictionary.

#parameter = clamdata['parameter_id']

#-- Invoke your actual system? --

# note the use of the shellsafe() function that wraps a variable in the
# specified quotes (second parameter) and makes sure the value doesn't break
# out of the quoted environment! Can be used without the quote too, but will be
# do much stricter checks then to ensure security.

#os.system("system.pl " + shellsafe(inputfilepath,'"') );

# Rather than execute a single system, call you may want to invoke it multiple
# times from within one of the iterations.

#A nice status message to indicate we're done
clam.common.status.write(statusfile, "Done",100) # status update

sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
