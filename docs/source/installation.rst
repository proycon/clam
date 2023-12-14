Installation
===================================

Installation
----------------

CLAM is available from the Python Package Index; a standardised
framework and repository for the installation of all kinds of Python
packages. This is the easiest method
of installing CLAM, as it will automatically fetch and install any
dependencies. We recommend to use a virtual environment if you
want to install CLAM locally as a user, if you insist to install globally,
prepend the following commands with ``sudo``:

CLAM is written for Python 3, which we will use in this documentation. Since CLAM version 3.0, backward compatibility with
Python 2.7 has been dropped.

Installing CLAM is as easy as issuing::

  $ pip install clam

If pip is not yet installed on your system, install it as follows (example for Debian/Ubuntu)::

  $ apt-get install python3-pip

However, we recommend you first create a Python Virtual Environment to install
CLAM (and your clam project) in. To create a virtual environment, which we name
*env* here (but you can choose any name you want), issue the following
command::

  $ python3 -m venv env

To enter the virtual environment, type the following (note the period)::

   $ . env/bin/activate

This will change your prompt by inserting the name of the virtual
environment. Now you can proceed to install CLAM in the virtual environment::

  $ pip install clam

You can verify the availability of CLAM by opening
an interactive Python interpreter and writing: ``import clam``

Installation Details
-------------------------

The following software is required to run CLAM, the installation process
explained above should obtain and install all the mandatory dependencies
automatically, except for Python itself:

-  python 3.6 or higher (2.7 is not supported since CLAM v3!)
-  flask
-  lxml
-  requests
-  requests-oauthlib
-  PyYAML
-  mysqlclient (optional, needed only for MySQL support)
-  FoLiA-Tools (optional, needed only for FoLiA support)

For development and testing, each CLAM webservice can run stand-alone on
any TCP port of your choice (make sure the port is open in your
firewall) using the built-in webserver. For production environments, it
is strongly recommended that you plug CLAM into a more advanced
webserver (Apache, nginx, lighttpd).

If you look in the directory where CLAM has been installed, the
following files may be of particular interest:

-  ``clamservice.py`` – The webservice itself; the command to be invoked
   to start it, installed as `clamservice`.
-  ``clamclient.py`` – A very generic CLAM client, to be used from the
   command-line, installed as `clamclient`.
-  ``clamdispatcher.py`` – The default dispatcher for launching wrapper
   scripts.
-  ``config/`` – The directory containing service configuration files.
   Place you service configuration here.
-  ``config/textstats.py`` – An example configuration.
-  ``common/`` – Common Python modules for CLAM.
-  ``common/parameters.py`` – Parameter-type definitions.
-  ``common/format.py`` – Format-type definitions.
-  ``common/data.py`` – CLAM Data API.
-  ``common/client.py`` – CLAM Client API.
-  ``static/style.css`` – The styling for visualisation; you can copy
   this to create your own styles.

Usage
-----------

Starting the service in stand-alone mode is done by launching ``clamservice`` with the name of your service
configuration. This standalone mode is intended primarily for development purposes and not recommended for production
use. The example below shows how to launch the supplied *“Text Statistics”* demo-service:

``$ clamservice clam.config.textstats``

Setting up the service to be used with an already existing webserver
requires some additional work. This is explained in later sections for
Apache and nginx.

Source Code Repository
---------------------------

The CLAM source code is hosted on `Github <https://github.com/proycon/clam>`_.

If you want to work with the latest development release of CLAM rather than the latest stable version. You can clone this git
repository as follows:

::

   $ git clone git://github.com/proycon/clam.git

This will create a directory ``clam`` in your current working directory.
To install CLAM globally or in your local Python virtual environment::

   $ pip install .

Use *sudo* for global installation, or ensure you are in a virtual
environment for local installation. Cloning from github directly is only
recommended for people who want to contribute to CLAM development
itself.

People migrating from very early versions of CLAM may have adopted a
workflow that uses the clam repository from github directly, without
running ``setup.py``. This is no longer supported and discouraged.
