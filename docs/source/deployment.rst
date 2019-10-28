.. _deployment:

Deployment in production
============================

In this section we assume you have your webservice all configured and working fine in development mode.
The next step is to move it into production mode, i.e. the final deployment on a webserver of your choice.

.. warning::

    Running with the built-in development server is not recommended for production as it offers sub-optimal performance,
    scalability, and security.

It is assumed you used the ``clamnewproject`` tool, as explained in :ref:`gettingstarted`, to get
started with your project. It generated various example configurations for production environments you can use.

Amongst the generated scripts is a WSGI script (recognisable by the ``wsgi`` extension). WSGI is a calling convention
for web servers to call Python applications and this script provides the initial entry-point, you most likely don't need
to edit it. Serving the python application is handled by uWSGI, which you can install (within your Python virtual
environment) as follows::

    $ pip install uwsgi

Your webservice project contains an ``ini`` file that provides the configuration for uwsgi to launch your webservice.
You can read the `uWSGI Documentation <https://uwsgi-docs.readthedocs.io/en/latest/>`_ for a full understanding, but the
generated template is commented and should generally be enough to get you going.

The uWSGI configuration is specific to the host you are running on so you will need to edit this ``ini`` file according
to your server. It contains the port the uWSGI process should listen on (note that this is by definition a *different*
port than the HTTP/HTTPS port you use to access your webserver!).  The shell script ``startserver_production.sh`` in
turn starts the uWSGI process with your webservice.

The next step is to forward requests from your webserver to this uWSGI process. Example configurations for nginx and
Apache have been generated automatically, adapt these and include them in your webserver configuration. There are
example configurations with a ``URLPREFIX``, i.e. when you are not hosting the webservice at the webserver root, and
without. Choose the one appropriate for your environment.

To use uWSGI with Apache, you need to install and enable the WSGI proxy module for Apache 2. On Debian/Ubuntu systems,
this is installed as follows::

   $ sudo apt-get install libapache2-mod-proxy-uwsgi

Apache configurations typically go into ``/etc/apache2/sites-enabled``, within a ``VirtualHost`` context.

For nginx, uWSGI support should already be compiled in. Configurations are commonly stored in ``/etc/nginx/conf.d/``. We assume the reader has sufficient experience with the webserver of his/her choice, and refer to the respective webserver's documentation for further details.


.. warning::

   It is *always* recommended to add some form of authentication or more
   restrictive access. You can either let CLAM handle authentication
   (*HTTP Basic or Digest Authentication* or *OAuth2*), or you can let
   your webserver itself handle authentication and not use CLAM’s authentication
   mechanism.

   You will also need to configure your firewall so the port of the uwsgi process (as configured in the ini file), is *NOT*
   open to the public, and only the HTTP/HTTPS port is.


.. _modwsgi:

Alternative deployment on Apache 2 with mod_wsgi
--------------------------------------------------

As an alternative to using Apache with uWSGI, you can use the older ``mod_wsgi`` module. For this you do not need the
uwsgi configuration (the ``ini`` file), nor the ``startserver_production.sh`` script.

#. Install ``mod_wsgi`` for Apache 2, if not already present on the
   system. In Debian and Ubuntu this is available as a package named
   ``libapache2-mod-wsgi`` for Python 2 and ``libapache2-mod-wsgi-py3``
   for Python 3. The latter is recommended for CLAM, but you can only
   have one installed at the same time.

#. Configure Apache to let it know about WSGI and your service. I assume
   the reader is acquainted with basic Apache configuration and will
   only elaborate on the specifics for CLAM. Adapt and add the following
   to any of your sites in ``/etc/apache2/sites-enabled`` (or optionally
   directly in ``httpd.conf``), within any ``VirtualHost`` context. Here
   it is assumed you configured your service configuration file with
   ``URLPREFIX`` set to *“yourservice”*.

   ::

       WSGIScriptAlias /yourwebservice \
        /path/to/yourwebservice/yourwebservice.wsgi/
       WSGIDaemonProcess yourwebservice user=username group=groupname \
           home=/path/to/yourwebservice threads=15 maximum-requests=10000
       WSGIProcessGroup yourservice
       WSGIPassAuthorization On
       Alias /yourwebservice/static \
         /usr/lib/python3.4/site-packages/clam-2.1-py3.4.egg/clam/static
       <Directory /path/to/clam/static/>
          Order deny,allow
          Allow from all
       </Directory>

   The ``WSGIScriptAlias`` and ``WSGIDaemonProcess`` directives go on
   one line, but were wrapped here for presentational purposes. Needless
   to say, all paths need to be adapted according to your setup and the
   configuration can be extended further as desired. Make sure to adapt
   the static alias to where CLAM is installed and where the directory
   is found, this depends on your installation and versions and is
   subject to change on an upgrade.

#. It is always recommended to add some form of authentication or more
   restrictive access. You can either let CLAM handle authentication
   (*HTTP Basic or Digest Authentication* or *OAuth2*), in which case
   you need to set ``WSGIPassAuthorization On``, as by default it is
   disabled, or you can let Apache itself handle authentication and not
   use CLAM’s authentication mechanism.

#. Restart Apache.

Note that we run WSGI in Daemon mode using the ``WSGIDaemonProcess`` and
``WSGIProcessGroup`` directives, as opposed to embedded mode. This is
the recommended way of using mod_wsgi, and is even mandatory when using
HTTP Basic/Digest Authentication. Whenever any code changes are made,
simply ``touch`` the WSGI file (updating its modification time), and the
changes will be immediately available. Embedded mode would require an
apache restart when modifications are made, and it may also lead to
problems with the HTTP Digest Authentication as authentication keys
(nonces) may not be retainable in memory due to constant reloads. Again
I’d like to emphasise that for authentication the line
``WSGIPassAuthorization On`` is vital, as otherwise user credentials
will never each CLAM.

For the specific options to the WSGIDaemonProcess directive you can
check http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives.
Important settings are the user and group the daemon will run as, the
home directory it will run in. The number of threads, processes, and
maximum-requests can also be configured to optimise performance and
system resources according to your needs.

Deploying CLAM with other webservers
--------------------------------------

The above configurations with Apache and Nginx are just the
configurations we tested. Other webservers (such as for example
lighttpd), should work too.


.. seealso::

    For configuration of authentication, see :ref:`auth`.
