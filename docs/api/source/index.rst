.. CLAM documentation master file, created by
   sphinx-quickstart on Mon Nov 29 17:12:57 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CLAM's documentation!
================================

CLAM allows you to quickly and transparently transform your Natural Language Processing application into a RESTful webservice, with which both human end-users as well as automated clients can interact. CLAM takes a description of your system and wraps itself around the system, allowing end-users or automated clients to upload input files to your application, start your application with specific parameters of their choice, and download and view the output of the application once it is completed.

CLAM is set up in a universal fashion, requiring minimal effort on the part of the service developer. Your actual NLP application is treated as a black box, of which only the parameters, input formats and output formats need to be described. Your application itself needs not be network aware in any way, nor aware of CLAM, and the handling and validation of input can be taken care of by CLAM.

CLAM is entirely written in Python, runs on UNIX-derived systems, and is available as open source under the GNU Public License (v3). It is set up in a modular fashion, and offers an API, and as such is easily extendable. CLAM communicates in a transparent XML format, and using XSL transformation offers a full web 2.0 web-interface for human end users. 

**This documentation only concerns the API**. F
For *full documentation* consult the `CLAM manual
<https://github.com/proycon/clam/raw/master/docs/clam_manual.pdf>`__, also accessible through the CLAM website
at http://proycon.github.io/clam . It is recommended to read this prior to
starting with this API documentation.

Contents:

.. toctree::
   :maxdepth: 3
   :glob:
   
   *
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

