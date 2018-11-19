.. _client:

Documentation for Service Clients
=================================

CLAM is designed as a RESTful webservice. This means a client
communicates with CLAM through the four HTTP verbs (GET/POST/PUT/DELETE)
on pre-defined URLs, effectively manipulating various resources. The
webservice will in turn respond with standard HTTP response codes and,
where applicable, a body in CLAM XML format.

When writing a client for a CLAM webservice, Python users benefit
greatly from the CLAM Client API, which in addition to the CLAM Data API
provides a friendly high-level interface for communication with a CLAM
webservice and the handling of its data. Both are shipped as an integral
part of CLAM by default. Using this API greatly facilitates writing a
client for your webservice in a limited amount of time, so it is an
approach to be recommended. Nevertheless, there are many valid reasons
why one might wish to write a client from scratch, not least as this
allows you to use any programming language of your choice, or better
integrate a CLAM webservice as a part of an existing application.

The :ref:`restspec` provides the full technical details necessary for an implementation of a
client. Moreover, each CLAM service offers an automatically tailored RESTful specification specific to the service, and
example client code in Python, by pointing your browser to your service on the path ``/info/``.

Users of the CLAM Client API can study the example client provided with
CLAM: ``clam/clients/textstats.py``. This client is heavily commented.

There is also a generic CLAM Client, ``clamclient``, which
offers a command line interface to *any* CLAM service.
The CLAM Client API enables users to quickly write clients to interact with CLAM webservices of any kind. It is an abstraction layer over all lower-level network communication. Consult also the CLAM Data API, as responses returned by the webservice are almost always instantiated as CLAMData objects in the client.

Client API Reference
---------------------

.. automodule:: clam.common.client
    :members:
    :undoc-members:

