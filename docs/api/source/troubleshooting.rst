Troubleshooting
====================

You may possibly encounter one of the following issues when attempting
to access your CLAM service through a browser:

#. **Apache gives an Internal Server Error (HTTP 500)** – Check your
   Apache error log to see what happened. For additional debug output by
   CLAM, set ``DEBUG=True`` in your CLAM service configuration file.

#. **I get an empty white page** – There is probably an error in loading
   the XSL stylesheet that renders the web application. Please use
   Firefox to verify, instead of Google Chrome or Internet Explorer, as
   it provides more detailed error output on XSLT transformations.

#. **I get “error loading stylesheet”** – The XSL stylesheet that
   renders the web-application can not be loaded. This is most likely
   due to a mismatch in URLs. The URL at which the webservice is
   accessed has to correspond exactly with the URL configured in the
   service configuration file, alternative hostnames or IPs will not
   work. Browsers refuse to load stylesheets from other sources for
   security reasons. Check your settings for HOST, PORT, and URLPREFIX,
   and whether you accessed the service by the same URL.

#. **I get an error “No template named response”** – Check whether
   ``CLAMDIR`` is set in your service configuration file and whether it
   points to the directory in which CLAM resides (the directory
   containing ``clamservice.py``)

#. **I’m using CLAM through Apache and mod_wsgi, but authentication does
   not work and I am always logged in as anonymous** – Check that
   ``WSGIPassAuthorization On`` is set in your Apache configuration, and
   ``USERS``, ``USERS_MYSQL`` or ``OAUTH`` is configured in your service
   configuration file.

#. **I am using ``URLPREFIX`` but CLAM tries to interpret the prefix as
   a project name** - This might happen in some WSGI setups. If this
   happens, set ``INTERNALURLPREFIX`` to the same value as
   ``URLPREFIX``. Always leave it empty in any other scenario.

Note that we strongly recommend developing your services using the
built-in webserver, and migrating to Apache, nginx or another webserver
when deploying your final service.

If you have a new issue, please use our `issue tracker <https://github.com/proycon/clam/issues>`_ to check whether it
has already been reported, and if not, report it yourself.
