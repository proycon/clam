.. _gettingstarted:

Getting Started
=================

Make sure you have first read the :ref:`introduction` so you understand what CLAM is and what its architecture is like.

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
various template files are created which are named after the
chosen identifier. You are expected to edit the service configuration
file, a Python script, as well as a host-specific configuration file and
one of the two system wrapper scripts (choose Python or shell script, or write
one from scratch in your favourite language). The scripts are heavily
commented to help you along, along with the documentation you are
reading, this should provide you with all knowledge necessary to make a
webservice.

-  ``myfirstproject/myfirstproject.py`` - Service Configuration File

-  ``myfirstproject/myfirstproject.config.yml`` - A more generic external configution file which is automatically
  included from the service configuration file unless a more host specific variant is found (``myfirstproject.$HOSTNAME.yml``). This will be
  addressed in :ref:`externalconf`.

-  ``myfirstproject/myfirstproject_wrapper.py`` - System Wrapper Script
   in Python (this is recommended over the shell version as it is suited for more
   complex webservices)

-  ``myfirstproject/myfirstproject_wrapper.sh`` - System Wrapper Script
   in shell script (only suggested for simple webservices)

-  ``myfirstproject/myfirstproject.wsgi`` - WSGI script, you probably
   don’t need to edit this

-  ``setup.py`` - Installation script (edit the metadata in here), run
   ``pip install .`` for installation in production
   environments or ``pip install -e`` for installation during
   development. (the start scripts mentioned below do this automatically
   for you)

-  ``Dockerfile`` - OCI Container build script. You may need to adapt this to add extra dependencies your system may need.

-  ``MANIFEST.in`` - Lists files to include in installation by ``setup.py``.

-  ``INSTRUCTIONS.rst`` - Automatically generated instructions. They complement/reiterate most of waht is said here.

Moreover, some scripts and sample configurations are generated:

-  ``startserver_development.sh`` - Start your webservice using the
   built-in development server.

-  ``startserver_production.sh`` - Start your webservice using the
   production server using uwsgi. To use this you will need to configure
   your webservice (e.g. Apache or nginx).

These template files need to be edited for your particular application.
They are heavily commented to guide you. The ``INSTRUCTIONS.rst`` file will
be created in your project directory and provides instructions on what
files to edit and how to start the clam service for your specific
project. Starting your webservice is as easy as running
``startserver_development.sh``, the script will inform you to what URL
to direct your browser once the webservice is running.

You can choose not to make use of one of the two generated system wrapper
scripts and instead either write one from scratch in another language of
your choice, or directly let CLAM invoke your application. Moreover, a
wrapper is only intended for CLAM's *project paradigm*, the *action paradigm* (:ref:`actions`) does
not make use of it at all.

Starting Your webservice
---------------------------

You can start your webservice in development mode with the included ``startserver_development.sh`` script, but not
before you first read how to construct your webservice. Read the :ref:`serviceconfig` documentation, and afterwards the :ref:`wrapperscript` documentation.

The start script simply installs your webservice and runs ``clamservice`` to run it, passing the module name of your
webservice configuration. Make sure you first activated your Python virtual environment (if used) when calling the start script.

For production environments, read the documentation on :ref:`deployment`.

Overriding host, port and urlprefix (advanced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``HOST``, ``PORT`` and ``URLPREFIX`` are configured in the service configuration file or the  host-specific external
configuration file it includes, CLAM will attempt to automatically guess them when they are not explicitly set. If you
run behind a reverse proxy (common in production environments), you will need to set ``USE_FORWARDED_HOST = True`` so
CLAM can automatically detect where the original request was coming from.

It is possible, however, to override these when
launching or deploying the webserver, without changing the service
configuration itself. If you use the development server, using
``clamservice``, then you can pass the ``-u`` flag with the full URL
CLAM should use. You can also set an environment variable
``CLAMFORCEURL``, which has the same effect. This latter option also
works when deploying CLAM through WSGI. The use of ``USE_FORWARDED_HOST`` is preferred though.


