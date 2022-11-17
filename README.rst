=======================================================
CLAM: Computational Linguistics Application Mediator
=======================================================

.. image:: https://github.com/proycon/clam/actions/workflows/clam.yml/badge.svg?branch=master
    :target: https://github.com/proycon/clam/actions/

.. image:: https://readthedocs.org/projects/clam/badge/?version=latest
    :target: http://clam.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://zenodo.org/badge/760072.svg
   :target: https://zenodo.org/badge/latestdoi/760072

.. image:: https://img.shields.io/pypi/v/clam
   :alt: Latest release in the Python Package Index
   :target: https://pypi.org/project/clam/

.. image:: http://applejack.science.ru.nl/lamabadge.php/clam
   :target: http://applejack.science.ru.nl/languagemachines/

.. image:: https://www.repostatus.org/badges/latest/active.svg
   :alt: Project Status: Active – The project has reached a stable, usable state and is being actively developed.
   :target: https://www.repostatus.org/#active


*by Maarten van Gompel*
*Centre for Language and Speech Technology, Radboud University Nijmegen*
*& KNAW Humanities Cluster*

*Licensed under GPLv3*

**Website:** https://proycon.github.io/clam
**Source repository:** https://github.com/proycon/clam/
**Documentation:** https://clam.readthedocs.io
**Installation:** ``pip install clam``

CLAM allows you to quickly and transparently transform your Natural Language
Processing application into a RESTful webservice, with which both human
end-users as well as automated clients can interact. CLAM takes a description
of your system and wraps itself around the system, allowing end-users or
automated clients to upload input files to your application, start your
application with specific parameters of their choice, and download and view the
output of the application once it is completed.

CLAM is set up in a universal fashion, requiring minimal effort on the part of
the service developer. Your actual NLP application is treated as a black box,
of which only the parameters, input formats and output formats need to be
described. Your application itself needs not be network aware in any way, nor
aware of CLAM, and the handling and validation of input can be taken care of by
CLAM.

CLAM is entirely written in Python, runs on UNIX-derived systems, and is
available as open source under the GNU Public License (v3). It is set up in a
modular fashion, and offers an API, and as such is easily extendable. CLAM
communicates in a transparent XML format, and using XSL transformation offers a
modern client-side generated web-interface for human end users.


Documentation
---------------

Documentation is available on https://clam.readthedocs.io

Some screenshots of the web user interface can be found below:

.. image:: https://raw.githubusercontent.com/proycon/clam/master/docs/screenshot.png
    :alt: the clam project list

.. image:: https://raw.githubusercontent.com/proycon/clam/master/docs/screenshot2.png
    :alt: the clam project page during staging

.. image:: https://raw.githubusercontent.com/proycon/clam/master/docs/screenshot3.png
    :alt: the clam project page when done


Installation
----------------

Installation from the Python Package Index using the  package manager *pip* it the recommended way to
intall CLAM. This is the easiest method
of installing CLAM, as it will automatically fetch and install any
dependencies. We recommend to use a virtual environment (``virtualenv``) if you
want to install CLAM locally as a user, if you want to install globally,
prepend the following commands with ``sudo``:

CLAM can be installed from the Python Package Index using pip. Pip is usually
part of the ``python3-pip`` package (Debian/Ubuntu) or similar, note that
Python 2.7 is not supported anymore (you might need to call ``pip3`` instead of ``pip`` on older system). It downloads CLAM and all dependencies
automatically:::

  $ pip install clam

If you already downloaded CLAM manually (from github), you can do::

  $ pip install .

If pip is not yet installed on your system, install it using:
 on debian-based linux systems (including Ubuntu)::

  $ apt-get install python3-pip

on RPM-based linux systems::

  $ yum install python3-pip

Note that sudo/root access is needed to install globally. Ask your system administrator
to install it if you do not own the system. Alternatively, you can install it locally in a Python virtual
environment::

  $ virtualenv --python=python3 env

Or::

  $ python3 -m venv env

Then activate it as follows:

  $ . env/bin/activate

  (env)$ pip install clam

CLAM also has some optional dependencies. For MySQL support, install
``mysqlclient`` using pip. For `FoLiA <https://proycon.github.io/folia>`_
support, install ``FoLiA-Tools`` using pip.

**Note:** CLAM is designed for Linux-like systems, although the client and data library work everywhere, hosting webservices via ``clamservice`` may not work on Windows.

Running a test webservice
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you installed CLAM using the above method, then you can launch a clam test
webservice using the development server as follows::

  $ clamservice -H localhost -p 8080 clam.config.textstats

Navigate your browser to http://localhost:8080 and verify everything works

**Note:** It is important to regularly keep CLAM up to date as fixes and
improvements are implemented on a regular basis. Update CLAM using::

  $ pip install -U clam


