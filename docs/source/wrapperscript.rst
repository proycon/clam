Wrapper script
===================

Service providers are encouraged to write a wrapper script that acts as
the glue between CLAM and the NLP Application(s). CLAM will execute the
wrapper script, and the wrapper script will in turn invoke the actual
NLP Application(s). Using a wrapper script offers more flexibility than
letting CLAM directly invoke the NLP Application, and allows the NLP
Application itself to be totally independent of CLAM.

When CLAM starts the wrapper script, it creates a ``clam.xml`` file containing the selection of parameters and input
files provided by the user.  It call the wrapper script with the arguments as specified in ``COMMAND`` in
the service configuration file (see `here <#command>`_).
There are some important things to take into account:

-  All user-provided input has to be read from the specified input
   directory. A full listing of this input will be provided in the
   ``clam.xml`` data file. If you choose not to use this, but use
   ``$PARAMETERS`` instead, then you must take care that your
   application can identify the file formats by filename, extension or
   otherwise.

-  All user-viewable output must be put in the specified output
   directory. Output files must be generated in accordance with the
   profiles that describe this generation.

-  The wrapper should periodically output a small status message to
   ``$STATUSFILE``. While this is not mandatory, it offers valuable
   feedback to the user on the state of the system.

-  The wrapper script is always started with the current working
   directory set to the selected project directory.

-  Wrapper scripts often invoke the actual application using some kind
   of ``system()`` call. Take care never to pass unvalidated user-input
   to the shell! This makes you vulnerable for code injection attacks.
   The CLAM Data API offers the function
   ``clam.common.data.shellsafe()`` to help protect you.

The wrapper script can be written in any language. Python developers
will have the big advantage that they can directly tie into the CLAM
Data API, which handles things such as reading the ``clam.xml`` data
file, makes all parameters and input files (with metadata) directly
accessible, and offers a function to protect your variables against code
injection when passing them to the shell. Using the Python for your
wrapper is therefore recommended.

If you used ``clamnewproject`` to begin your new clam service, two
example wrapper scripts will have been created for you, one in Python
using the CLAM Data API, and one using bash shell script. Choose one.
These generated scripts are heavily commented to guide you in setting
your wrapper script up. This documentation will add some further
insights.

Data API
--------------

The key function of CLAM Data API is to parse the CLAM XML Data file
that the clam webservice uses to communicate with clients. This data is
parsed and all its components are made available in an instance of a
:class:`CLAMData` class.

Suppose your wrapper script is called with the following command
definition:

.. code-block:: python

   COMMAND = "/path/to/wrapperscript.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY"

Your wrapper scripts then typically starts in the following fashion:

.. code-block:: python

   import sys
   import clam.common.data

   datafile = sys.argv[1]
   statusfile = sys.argv[2]
   outputdir = sys.argv[3]

   clamdata = clam.common.data.getclamdata(datafile)

The first statements parse the command line arguments. The last
statement returns a :class:`CLAMData`` instance, which contains all data your
wrapper might need, representing the state of the project and all user
input. It is highly recommended to read the API reference for :class:`CLAMData`. A few of the attributes available are:

-  ``clamdata.system_id``

-  ``clamdata.project``

-  ``clamdata.user``

-  ``clamdata.status``

-  ``clamdata.parameters``

-  ``clamdata.input``

-  ``clamdata.program``

Any global parameters set by the user are available from the
``clamdata`` instance, by using it like a Python dictionary, where the
keys correspond to the Parameter ID:

.. code-block:: python

   parameter = clamdata['parameter_id']

The CLAM API also has facilities to use a status file to relay progress
feedback to the web-interface. Using it is as simple as importing the
library and writing messages at strategic points during your program’s
execution:

.. code-block:: python

   import clam.common.status
   clam.common.status.write(statusfile, "We are running!")

Progress can also be expressed through an additional completion
parameter, holding a value between :math:`0` and :math:`1`. The
web-application will show a progress bar if such information is
provided:

.. code-block:: python

   clam.common.status.write(statusfile,
        "We're half way there! Hang on!", 0.5)

If you have a specific input file you want to grab, you may obtain it
from your ``clamdata`` instance with `:meth:`CLAMData.inputtemplate`:

.. code-block:: python

   inputfile = clamdata.inputfile('some-inputtemplate-id')
   inputfilepath = str(inputfile)

The variable ``inputfile`` in the above example is an instance of :class:`CLAMFile`, ``inputfilepath`` in the above
example will contain the full path to the file that was uploaded by the user for the specified input template.

Once you have a file, you can easily obtain any associated metadata
parameters in a dictionary-like fashion, for instance:

.. code-block:: python

   author = inputfile.metadata['author']

When you have multiple input files, you may want to iterate over all of
them. The name of the inputtemplate can be obtained from the metadata:

.. code-block:: python

   for inputfile in clamdata.input:
       inputfilepath = str(inputfile)
       inputtemplate = inputfile.metadata.inputtemplate

The core of your wrapper script usually consists of a call to your
external program. In Python this can be done through ``os.system()``.
Consider the following fictitious example of a program that translates
an input text to the language specified by a global parameter.

.. code-block:: python

   os.system("translate -l " + clamdata['language'] + " " + \
    str(clamdata.inputfile('sourcetext')) + \
    + " > " + outputdir + "/output.txt"))

However, at this point you need to be aware of possible malicious use,
and make sure nobody can perform a code injection attack. The key here
is to never pass unvalidated data obtained from user-input directly to
the shell. CLAM’s various parameters have their own validation options;
the only risk left to mitigate is that of string input. If the global
parameter *language* would be a free string input field, a user may
insert malicious code that gets passed to the shell. To prevent this,
use the ``shellsafe()`` function from the CLAM Data API.

.. code-block:: python

   shellsafe = clam.common.data.shellsafe #just a shortcut

   os.system("translate -l " + shellsafe(clamdata['language'],"'") + \
    " " + \
    shellsafe(str(clamdata.inputfile('sourcetext')),'"') + \
    " > " + shellsafe(outputdir + "/output.txt") ))

Each variable should be wrapped in ``shellsafe``. The second argument to
shellsafe expresses whether to wrap the variable in quotes, and if so,
which quotes. Quotes are mandatory for values containing spaces or other
symbols otherwise forbidden. If no quotes are used, shellsafe does more
stringent checks to prevent code injection. A Python exception is raised
if the variable is not deemed safe, and the shell will not be invoked.
CLAM itself will detect and produce an error log.

.. _program:

Program
~~~~~~~

A *program* (programme) describes exactly what output files will be
generated on the basis of what input files. It is the concretisation of
the profiles. Profiles specify how input relates to output in a generic
sense, using input and output templates. The program lists what exact
output files will be generates, with filenames, on the basis of exactly
which input files. The program is a read-only construct generated from
the profiles and the input. It is present in the CLAM XML response, the
clam XML data file, and accessible to your wrapper script.

Keep in mind that this method allows you to iterate over the output
files prior to their actual creation. Because it contains exact
information on output and input files. It is the most elegant method to
set up your wrapper script, avoiding any duplication of file names and
allowing your wrapper to be set up in a filename agnostic way.

In the following example. We obtain all output files and corresponding
output templates using the :meth:`CLAMData.getoutputfiles`. For each output file,
we can request the input files (and corresponding input templates) using
the :meth:`CLAMData.getinputfiles`.

Consider the following example that simply concatenates all input texts
(input template ``inputtext``) to a single output text (output template
``outputtext``) using the unix ``cat`` tool:

.. code-block:: python

   for outputfile, outputtemplate in clamdata.program.getoutputfiles():
     outputfilepath = str(outputfile)
     if outputtemplate == 'outputtext':
       inputfiles_safe = ""
       for inputfile, inputtemplate in clamdata.program.getinputfiles(outputfilename):
           inputfilepath = str(inputfile)
           if inputtemplate == 'inputtext': #check is a bit obsolete in this case
               inputfiles_safe += " " + shellsafe(inputfilepath)
       if inputfiles_safe:
           os.system("cat " + inputfiles_safe + " > " + shellsafe(outputfilepath))

The ``outputfile`` and ``inputfile`` variables are again instances of :class:`CLAMFile`.
Their metadata parameters can be accesses through
``outputfile.metadata[’parameter_id’]`` and
``inputfile.metadata[’parameter_id’]``.

Examples
--------

Some example webservice configuration files and wrapper scripts are
included in ``clam/config`` and ``clam/wrappers`` respectively, often
similarly named.

One notable examples that are heavily commented:

-  ``textstats`` – A simple text statistics/frequency list example for
   CLAM. It is a portable sample that has no external dependencies, the
   implementation is pure Python and done entirely in the wrapper
   script.

Some real-life CLAM webservice can be found in https://github.com/proycon/clamservices

Data API Reference
---------------------

.. automodule:: clam.common.data
    :members:
    :undoc-members:
