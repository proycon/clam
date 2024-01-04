.. _deployment:

Deployment in production
============================

In this section we assume you have your webservice all configured and working fine in development mode.
The next step is to move it into production mode, i.e. the final deployment on a webserver of your choice.

.. warning::

    Running with the built-in development server is not recommended for production as it offers sub-optimal performance,
    scalability, and security.

It is assumed you used the ``clamnewproject`` tool, as explained in
:ref:`gettingstarted`, to get started with your project.

Container deployment
------------------------

When running ``clamnewproject``, it generated a `Dockerfile` that is suitable
for production environments (since CLAM v3.2). This is the recommended way for
production deployments and works nicely in setups with Docker, Docker Compose,
Podman and/or Kubernetes. 

Please first ensure you have docker (or a compatible system like podman)
installed on your system. On Ubuntu/Debian::

    apt-get install docker.io

A ``startserver_production.sh`` script was generated that builds and subsequently runs the container. It builds the container as follows::

    docker build -t yourservice .

and runs it like::

    docker run --rm -v "/path/to/data:/data" -p 8080:80 yourservice


If you used the generated ``*.config.yml`` external configuration file, then
you can configure a lot of the deployment specific variables via environment
variables. Check the ``*.config.yml`` file to see which are available. Note
that most environment variables carry the additional prefix `CLAM_`.

The ``startserver_production.sh`` script generates a non-persistent data
directory on the host for use by the container, you most likely want to change
this either in the script itself or by setting a `DATADIR` environment variable
to an existing directory on the host prior to running the script!

The container is based on Alpine Linux and serves your CLAM webservice via
nginx and uwsgi.

When deploying in this way, it is strongly recommended that you run it behind a
reverse proxy that handles SSL, neither CLAM nor the provided container handles
HTTPS traffic directly. Always Make sure to pass environment variable
``--env CLAM_USE_FORWARDED_HOST=1`` when starting the container in such cases!

The container should be suitable for publication to container registries such
as Docker Hub or Quay.io, provided that you didn't hard-code any secrets in the
code or configuration.

Manual deployment
------------------------

If you do not want to use containers for your deployment, then you have to install and configure various components yourself.

We assume the reader has sufficient experience with the webserver of his/her
choice, and refer to the respective webserver's documentation for further
details.

1. Install and configure a webserver like nginx or apache. Here is an example snippet for nginx::

    #Nginx example configuration using uwsgi (assuming your service runs at the root of the server!) include this from your server block in your nginx.conf
    location /static { alias /usr/lib/python3.10/site-packages/clam/static; }
    location / { try_files $uri @yourservice; }
    location @yourservice {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:8888;
    }

And here is one for Apache via `mod-uwsgi-proxy` (make sure it is installed). Apache configurations typically go into ``/etc/apache2/sites-enabled``, within a ``VirtualHost`` context::

    #Apache example configuration assuming your service runs at the virtualhost root!) insert this in your VirtualHost in your Apache configuration

    ProxyPass / uwsgi://127.0.0.1:8888/

    #You will likely need to adapt the reference to path /tmp/env/lib/python3.10/site-packages/clam if you move this to another system
    Alias /static /usr/lib/python3.10/site-packages/clam/static
    <Directory /usr/lib/python3.10/site-packages/clam/static/>
        Order deny,allow
        Allow from all
    </Directory>

2. Install uwsgi, it acts as the gateway between the webserver and CLAM. On Debian/Ubuntu::

    apt install uwsgi uwsgi-plugin-python3

3. Configure uwsgi. Here is an example ini file for uwsgi::

    [uwsgi]
    socket = 127.0.0.1:8888
    master = true
    plugins = python3,logfile
    logger = file:/path/to/yourservice/yourservice.uwsgi.log
    mount = /=/path/to/yourservice/yourservice/yourservice.wsgi
    processes = 2
    threads = 2
    #the following option is needed for nginx, maybe not for Apache?
    manage-script-name = yes
    #set this if you installed the service in a virtual environment (recommended)
    #virtualenv = /path/to/env
    #chdir = /path/to/env
    #Optionally, this is also a place where you can inject environment variables for CLAM:
    env = CLAM_ROOT=/data/yourservice-userdata
    env = CLAM_USER_FORWARDED_HOST=1
 
4. The service can now be started with ``uwsgi yourservice.ini``. But you'll want to configure the uwsgi server to auto-start. You can use either uwsgi emperor and have the above ini file as a so-called vassal, or you can use your system's init system (e.g. systemd).

.. warning::

   It is *always* recommended to add some form of authentication or more
   restrictive access. You can either let CLAM handle authentication
   (*HTTP Basic or Digest Authentication* or *OAuth2*), or you can let
   your webserver itself handle authentication and not use CLAM’s authentication
   mechanism.

   You will also need to configure your firewall so the port of the uwsgi process (as configured in the ini file), is *NOT*
   open to the public, and only the HTTP/HTTPS port is.


.. _modwsgi:

Manual deployment: alternative deployment on Apache 2 with mod_wsgi
--------------------------------------------------

As an alternative to using Apache with uWSGI, you can use the older ``mod_wsgi`` module. For this you do not need the
uwsgi configuration (the ``ini`` file), nor the ``startserver_production.sh`` script.

#. Install ``mod_wsgi`` for Apache 2, if not already present on the
   system. In Debian and Ubuntu this is available as a package named
   ``libapache2-mod-wsgi-py3``.

#. Configure Apache to let it know about WSGI and your service:

   ::

       WSGIScriptAlias / /path/to/yourwebservice/yourwebservice.wsgi/
       WSGIDaemonProcess yourwebservice user=username group=groupname \
           home=/path/to/yourwebservice threads=15 maximum-requests=10000
       WSGIProcessGroup yourservice
       WSGIPassAuthorization On

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

The above configurations with Apache and Nginx are just the configurations we
tested. Other webservers (such as for example lighttpd), should work too. It is
also conceivable to use other WSGI middleware instead of uwsgi (such as gunicorn or mod_wsgi).

.. seealso::

    For configuration of authentication, see :ref:`auth`.

Deploying CLAM behind a reverse proxy
--------------------------------------

In production environment, you will often deploy your webservice behind a
reverse proxy. This is recommended. If this is the case, then you will want to
invoke the container with ``--env CLAM_USE_FORWARDED_HOST=1``, or alternatively
set `use_forwarded_host: true` in the external configuration yaml file directly.
CLAM can now detect the original host and protocol it was called with. This
expects your reverse proxy to set the proper ``X-Forwarded-Host`` and
``X-Forwarded-Proto`` headers, and is a security risk if these headers are not
set but are forwarded from actual end-users.

The other alternative is to set ``forceurl`` in the external configuration
yaml file to the exact URL where your webservice will run. But this implies
that it won't work properly when invoked with another URL and is therefore not
recommended.


