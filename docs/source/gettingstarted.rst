.. _gettingstarted:

Getting Started
=================

You start a new CLAM webservice project using the ``clamnewproject`` tool. The tool
generates all the necessary files, which you have to edit. The tool
takes one argument: an identifier for your system. This identifier is
for internal use, possibly for use in URLs, paths, and filenames. It may not
not contain any spaces or other special characters. Mind that this
ID is case sensitive, so it is strongly recommended to keep it all lower
case. Example:

::

   $ clamnewproject myfirstproject

The tool will create a directory named after the identifier, in which
various template files are created which are similarly named after the
chosen identifier. You are expected to edit the service configuration
file, a Python script, as well as a host-specific configuration file and
one of the two system wrapper scripts (choose Python or Bash, or write
one from scratch in your favourite language). The scripts are heavily
commented to help you along, along with the documentation you are
reading, this should provide you with all knowledge necessary to make a
webservice.

-  ``myfirstproject/myfirstproject.py`` - Service Configuration File

-  ``myfirstproject/myfirstproject.$HOSTNAME.yml`` - Host-specific
   external configution file which is automatically included from the
   service configuration file if ran on the specified host. This will be
   addressed `later <#externalconf>`_.

-  ``myfirstproject/myfirstproject_wrapper.py`` - System Wrapper Script
   in Python (this is recommended over the bash version, suited for more
   complex webservices)

-  ``myfirstproject/myfirstproject_wrapper.sh`` - System Wrapper Script
   in Bash (only suggested for simple webservices)

-  ``myfirstproject/myfirstproject.wsgi`` - WSGI script, you probably
   don’t need to edit this

-  ``setup.py`` - Installation script (edit the metadata in here), run
   ``python setup.py install`` for installation in production
   environments or ``python setup.py develop`` for installation during
   development. (the start scripts mentioned below do this automatically
   for you)

-  ``INSTRUCTIONS.rst`` - Automatically generated instructions

Moreover, some scripts and sample configurations are generated:

-  ``startserver_development.sh`` - Start your webservice using the
   built-in development server

-  ``startserver_production.sh`` - Start your webservice using the
   production server using uwsgi. To use this you will need to configure
   your webservice (e.g. Apache or nginx).

-  ``myfirstproject.$HOSTNAME.ini`` - Uwsgi configuration (for a
   specific host), used for production environments

-  ``*.conf`` - Sample configuration files for production environments
   using a Apache 2 or Nginx webserver. Consult the section on `deployment <#deployment>`_ for details.

These template files need to be edited for your particular application.
They are heavily commented to guide you. The ``INSTRUCTIONS.rst`` file will
be created in your project directory and provides instructions on what
files to edit and how to start the clam service for your specific
project. Starting your webservice is as easy as running
``startserver_development.sh``, the script will inform you to what URL
to direct your browser once the webservice is running.

You can choose not to make use of one of the generated system wrapper
scripts and instead either write one from scratch in another language of
your choice, or directly let CLAM invoke your application. Moreover, a
wrapper is intended for the project paradigm, the `action paradigm <#actions>`_ does
not make use of it.

Starting Your webservice
---------------------------

You can start your webservice in development mode with the included ``startserver_development.sh`` script, but not
before you first read how to construct your webservice. Read the the `service configuration <#serviceconfig>`_ documentation, and afterwards the `wrapper script <#wrapperscript>`_ documentation.

The start script simply installs your webservice and runs ``clamservice`` to run it, passing the module name of your
webservice configuration. Make sure you first activated your Python virtual environment (if used) when calling the start script.

For production environments, read the documentation on `deployment <#deployment>`_.

Overriding host, port and urlprefix (advanced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``HOST``, ``PORT`` and ``URLPREFIX`` are configured in the service configuration file or the  host-specific external
configuration file it includes, CLAM will attempt to automatically guess them when they are not explicitly set.

It is possible, however, to override these when
launching or deploying the webserver, without changing the service
configuration itself. If you use the development server, using
``clamservice``, then you can pass the ``-u`` flag with the full URL
CLAM should use. You can also set an environment variable
``CLAMFORCEURL``, which has the same effect. This latter option also
works when deploying CLAM through WSGI.

The most common use for this is when serving CLAM behind another reverse
proxy, where automatic hostname detection could never work.

