.. _restspec:

RESTful API specification
=============================

This appendix provides a full specification of the RESTful interface to
CLAM.


.. note::

    Note that for each webservice, an auto-generated and human readable RESTful API specification is available at the ``/info/``
    endpoint which provides a more tailored overview. This info page also presents auto-generated example code for
    interacting with the webservice.

General Webservice Information
--------------------------------

:Endpoint: ``/porch/`` or ``/info/`` (or ``/`` if no authentication credentials are provided)
:Method: ``GET``
:Request Parameters:  (none)
:Description: Retrieves the general webservice specification (profiles, formats, etc). This also works without
              authentication even on authenticated webservices (unless explicitly disabled). ``/porch/`` and ``/info/``
              and almost identical from a webservice perspective, but render very differently in the browser.
:Response: ``200 - OK`` & CLAM XML

Project Index
------------------------

:Endpoint: ``/index/`` (or ``/`` if proper authentication credentials are provided)
:Method: ``GET``
:Request Parameters:  (none)
:Description: Retrieves the project index and general webservice specification
:Response: ``200 - OK`` & CLAM XML, ``401 - Unauthorised``

Project Endpoint
-------------------

:Endpoint: ``/[project]/``
:Method: ``GET``
:Request Parameters: (none)
:Response: ``200 - OK`` & CLAM XML, ``401 - Unauthorised``,
  ``404 - Not Found``
:Description: This returns the current state of the project in
  CLAM XML format. Depending on the state this contains a specification
  of all accepted parameters, all input files, and all output files.
  Note that errors in parameter validation are encoded in the CLAM XML
  response; the system will still return a 200 response.
:Method: ``PUT``
:Request Parameters: (none)
:Response: ``201 - Created``, ``401 - Unauthorised``,
  ``403 - Forbidden`` *(Invalid project ID)*, ``403 - Forbidden`` *(No project name)*
:Description: This is necessary before attempting to upload any
  files; it initialises an empty new project.
:Method: ``POST``
:Request Parameters: Accepted parameters are defined in the
  Service Configuration file (and thus differ per service). The
  parameter ID corresponds to the parameter keys in the request
  parameters
:Response: ``202 - Accepted`` & CLAM XML, ``401 - Unauthorised``,
  ``404 - Not Found``, ``403 - Permission Denied`` & CLAM XML,
  ``500 - Internal Server Error``
:Description: This starts the running of a project, i.e. starts
  the actual background program with the specified service-specific
  parameters and provided input files. The parameters are provided in
  the query string; the input files are provided in separate POST
  requests to ``/[project]/input/[filename]``, prior to this query. If
  any parameter errors occur or no profiles match the input files and
  parameters, a 403 response will be returned with errors marked in the
  CLAM XML. If a ``500 - Server Error`` is returned, CLAM most likely is
  not able to invoke the underlying application or the server has
  insufficient free resources.
:Method: ``DELETE``
:Request Parameters: The parameter ``abortonly`` can be set to 1
  if you only want to abort a running process without deleting the
  entire project
:Response: ``200 - OK``, ``401 - Unauthorised``,
  ``404 - Not Found``
:Description: Deletes a project. Any running processes will be
  aborted.

Input files
--------------


:Endpoint: ``/[project]/input/[filename]``
:Method: ``GET``
:Request Parameters: (none)
:Response: ``200 - OK`` & File contents, ``401 - Unauthorised``,
  ``404 - Not Found``
:Description: Retrieves the specified input file.


:Method: ``DELETE``
:Request Parameters: (none)
:Response: ``200 - OK`` & File contents, ``401 - Unauthorised``,
  ``404 - Not Found``
:Description: Deletes the specified input file.


:Endpoint: ``/[project]/input/[filename]`` or
  ``/[project]/input/[inputtemplate]/[filename]``
:Method: ``POST``
:Request Parameters: ``inputtemplate=[inputtemplate\_id]``
  ``file=[HTTP file]*`` ``url=[download-url]*``
  ``contents=[text-content]*`` ``metafile=[HTTP file]``
  ``metadata=[CLAM Metadata XML]`` Other accepted parameters are defined
  in the various Input Templates in the Service Configuration file (and
  thus differs per service and input template). The parameter ID
  corresponds to the parameter keys in the query string.
:Response: ``200 - OK`` & CLAM-Upload XML, ``403 - Permission Denied`` & CLAM-Upload XML,
  ``401 - Unauthorised``, ``404 - Not Found``
:Description: This method adds a new input file, which is
  transmitted in the ``multipart/form-data`` encoding along with request
  parameters and metadata parameters. . The response is returned in
  CLAM-Upload XML (distinct from CLAM XML!). Two arguments are
  mandatory: the input template, which designates what kind of file will
  be added and points to one of the InputTemplate IDs the webservice
  supports, and *one of the* query arguments marked with an asterisk.
  Adding a file can proceed either by uploading it from the client
  machine ``(file)``, by downloading it from another URL ``(url)``, or
  by passing the contents in the POST message itself ``(contents)``.
  Only one of these can be used at a time. Metadata can be passed in
  *three* different ways: 1) by simply specifying a metadata field as
  request parameters, with the same ID as defined in the input template.
  2) setting the ``metafile`` attribute to an HTTP file, or 3) by
  setting ``metadata`` to the full XML string of the metadata
  specification.


:Endpoint: ``/[project]/input/[filename]/metadata``
:Method: ``GET``
:Request Parameters: (none)
:Response: ``200 - OK`` & CLAM Metadata XML,
  ``401 - Unauthorised``, ``404 - Not Found``
:Description: Retrieves the metadata for the specified input file.

Output Files
----------------


:Endpoint: ``/[project]/output/[filename]``
:Method: ``GET``
:Request Parameters: (none)
:Response: ``200 - OK`` & File contents, ``401 - Unauthorised``,
  ``404 - Not Found``
:Description: Retrieves the specified output file.
:Method: ``DELETE``
:Request Parameters: (none)
:Response: ``200 - OK`` & File contents, ``401 - Unauthorised``,
  ``404 - Not Found``
:Description: Deletes the specified output file.


:Endpoint: ``/[project]/output/[filename]/metadata``
:Method: ``GET``
:Request Parameters: (none)
:Response: ``200 - OK`` & CLAM Metadata XML,
  ``401 - Unauthorised``, ``404 - Not Found``
:Description: Retrieves the metadata for the specified output
  file.


Archive Download
~~~~~~~~~~~~~~~~~~

:Endpoint: ``/[project]/output/``
:Method: ``GET``
:Request Parameters: ``format=zip|tar.gz|tar.bz2``
:Response: ``200 - OK`` & File contents, ``401 - Unauthorised``,
  ``404 - Not Found``
:Description: Offers a single archive, of the desired format,
  including all output files
:Method: ``DELETE``
:Request Parameters: (none)
:Response: ``200 - OK`` & File contents, ``401 - Unauthorised``
:Description: Deletes all output files and resets the project for
  another run.


Actions
-----------

:Endpoint: ``/actions/[action_id]/``
:Method: ``GET`` and/or ``POST``, may be constrained by the action
:Request Parameters: Determined by the action
:Response: ``200 - OK`` & Result data determined by the action,
  ``401 - Unauthorised``, ``404 - Not Found``
:Description: This is a remote procedure call to run the specified
  action and obtain the results. The parameters are specific to the
  action.

Project entry shortcut
---------------------------

This is a shortcut method (available since CLAM v0.99.17) that
  combines the steps of project creation, file adding and upload, in one
  single GET or POST request. Although more limited than the invididual
  calls, and less RESTful, it facilitates the job for simpler callers:


:Endpoint: ``/``
:Method: ``GET`` or ``POST``
:Request Parameters: ``project=[name|new]`` (mandatory), selects
  and if necessary creates the project with the specified name. If the
  value is set to *new*, a random project name will be generated.
  ``{inputtemplate}=[contents]`` – Pass file contents for the specified
  input templateJ (the variable name is the inputtemplate ID), this
  corresponds to the ``contents`` variable in the non-shortcut method.
  ``{inputtemplate}_url=[url]`` – Pass a url where to obtain the file
  for the specified input templateJ (the variable name contains the
  inputtemplate ID), this corresponds to the ``url`` variable in the
  non-shortcut method. ``{inputtemplate}_filename=[filename]`` – Sets
  the desired filename for the specified input template, use in
  combination with one of the two parameters above. Not needed when the
  webservice assigns a fixed filename. ``start=[0|1]`` – Set this
  parameter to 1 if you want the project to start automatically. The
  default is not to start automatically. Other accepted parameters are
  defined in the Service Configuration file (and thus differ per
  service). For global parameters, the parameter ID corresponds to the
  parameter keys in the request parameters, for parameters pertaining to
  a specific input template, prepend the ID of the input template and an
  underscore to the parameter ID (``{inputtemplate}_``).
:Response: ``200 - OK`` & CLAM XML, ``401 - Unauthorised``,
  ``403 - Permission denied``

If OAuth authentication is enabled and no access token is passed, almost
all URLs return ``HTTP 303 - See Other`` and redirect to the
authentication provider. At this stage, user input may be required,
stopping automated clients. After the user input, or if no user input is
required, the authorization provider should relay the user back to a
special CLAM login page with another ``HTTP 303``. This implies the
client should then redo the request with the proper access token. See
the section on OAuth2 authentication for more details.
