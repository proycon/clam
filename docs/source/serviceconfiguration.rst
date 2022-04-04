.. _serviceconfig:

Service configuration
============================

The service configuration consists of a description of your NLP
application, or rather, a description of the system wrapper script that
surrounds it. It specifies what parameters the system can take, and what
input and output formats are expected under what circumstances. The
service configuration is itself a Python script, but knowledge of Python
is not essential for you to be able to make your own service
configurations.

It is strongly recommended, but not mandatory, to separate the parts of the configuration that are host-specific configuration
settings from the parts that are generic. Host-specific configurations is stored in :ref:`externalconf` that are dynamically included from the service configuration script. Doing so facilitates distribution and deployment on different systems late.

It is assumed you are using the ``clamnewproject`` tool as explain in :ref:`gettingstarted`, which
generates a template service configuration you can edit, including a host-specific external configuration name
recognisable by the ``yml`` extension. When reading this section, it may help your understanding to inspect these files
alongside.

One of the first things to configure is the root path (``ROOT``). All projects created in the webservice will be
confined to the ``projects/`` directory within this root path, each project having its own subdirectory. When your
underlying application or wrapper script is launched, the current working directory will be set to this project
directory.

The ``ROOT`` directory will be automatically created upon the first run.

General Webservice Metadata
-------------------------------

The following general metadata fields are available, setting them is strongly recommended:

* ``SYSTEM_ID`` - The System ID, a short alphanumeric identifier for internal use only **(mandatory!)**
* ``SYSTEM_NAME`` - System name, the way the system is presented to the world
* ``SYSTEM_DESCRIPTION`` - An informative description for this system (this should be fairly short, about one paragraph, and may not contain HTML). If you want a more extensive description in the interface, possibly with HTML then see :ref:`custominterface`.
* ``SYSTEM_VERSION`` - A version label of the underlying tool and/or this CLAM wrapper.
* ``SYSTEM_AUTHOR`` - The author(s) of the underlying tool and/or this CLAM wrapper
* ``SYSTEM_EMAIL`` - A single contact e-mail address
* ``SYSTEM_URL`` - An assocated website, either for this webservice or the underlying software.
* ``SYSTEM_PARENT_URL`` - You can set this to a website URL if this webservice embedded in a larger system? Like part of an institution or particular portal site. A small link back to this site will be generated in the navigation bar of the interface.
* ``SYSTEM_COVER_URL`` - The URL of a cover image to prominently display in the header of the interface. You may also want to set ``INTERFACEOPTIONS="centercover"`` to center it horizontally.
* ``SYSTEM_REGISTER_URL`` - URL to a website where users can register an account for use with this webservice. This
  link is only for human end-users, no API endpoint.

.. _sadmin:

Server Administration
-------------------------

The host-specific part of the configuration contains first of all the hostname and the port where the webservice will be
hosted. If not configured, automatic detection is attempted.

When CLAM runs in a production environment (see :ref:`deployment`) using an existing webserver without its
own virtual host, it is often configured at a different URL rather than at the webserver root. In this case, the value
of ``URLPREFIX`` should be configured accordingly. If you want your webservice to run at
http://yourhost.com/yourwebservice/ for instance, then the ``URLPREFIX`` should be set to ``yourwebservice``.

.. note::

    In rare cases where the URL wrongly
    propagates to CLAM (i.e. CLAM tries to interpret your urlprefix as a
    project), you need to set ``INTERNALURLPREFIX`` to the same value. This
    might happen in certain WSGI set-ups, leave it unset in all other
    scenarios.

In order to keep server load manageable, three methods are configurable
in the service configuration file. First, you can set the variable
``REQUIREMEMORY`` to the minimum amount of free memory that has to be
available (in megabytes, and not considering swap memory!). If not
enough memory is free, users will not be able to launch new processes,
but will receive an HTTP 500 error instead. Second, there is the
``MAXLOADAVG`` variable; if the 5-minute load average exceeds this
number, new processes will also be rejected. Third, there is
``MINDISKSPACE`` and ``DISK``. This sets a constraint on the minimum
amount of free disk space in megabytes on the specified DISK (for
example: ``/dev/sda1``), which should be the disk holding ``ROOT``. If
any of these values is set to zero, the checks are disabled. Note though
that this makes your system vulnerable to denial-of-service attacks by
possibly malicious users, especially if no user authentication is
configured!

Further constraints on disk space can be placed by setting the following:
* ``USERQUOTA`` - Maximum size in MB of all projects for a user. If this is exceeded no new projects can be created or
  started.
* ``PROJECTQUOTA`` - Maximum size in MB of any single project. Larger projects can not be started.
* ``MAXCONCURRENTPROJECTSPERUSER`` - Maximum number of projects that a single user can run concurrently.

Extra resource control is handled by the CLAM Dispatcher; a small
program that launches and monitors your wrapper script. In your service
configuration file you can configure the variable
``DISPATCHER_MAXRESMEM`` and ``DISPATCHER_MAXTIME``. The former is the
maximum memory consumption of your process, in megabytes. The latter is
the maximum run-time of your process in seconds. Programs that exceed
this limit will be automatically aborted. The dispatcher will check with
a certain interval, configured in ``DISPATCHER_POLLINTERVAL`` (in
seconds), if the limits have been exceeded it will take the necessary
action.

If for some reason you do not want to make use of the web-based user
interface in CLAM, then you can disable it by setting
``ENABLEWEBAPP = False``. Note that this is **not in any way** a security measure!
Everything is technically still as accessible. You can also disable
project listing, in which case projects are only accessible if users
know the exact project name. Set ``LISTPROJECTS = False``.

CLAM offers a limited web-based administrative interface that allows you
to view what users and projects there are, access their files, abort
runs, and delete projects. This interface can be accessed on the
``/admin/`` URL, but requires that the logged-in user is in the list of
``ADMINS`` in the service configuration file. The administrative
interface itself does not, and will never, offer any means to adjust
service configuration options.


.. _auth:

User Authentication
----------------------------

Being a RESTful webservice, user authentication proceeds over HTTP
itself. CLAM implements HTTP Basic Authentication, HTTP Digest
Authentication [Franks1999]_ and OAuth2
[Hardt2012]_. HTTP Digest Authentication, contrary to HTTP
Basic Authentication, computes a hash of the username and password
client-side and transmits that hash, rather than a plaintext password.
User passwords are therefore only available to CLAM in hashed form and
are not transmitted unencrypted, even over a HTTP connection. HTTP Basic
Authentication, conversely, should only be use over SSL (i.e. HTTPS),
and CLAM will by default disallow it if it thinks it’s not running on an
SSL connection.

CLAM itself does not provide SSL on the built-in development server as
this is delegated to your production webserver (Apache or Nginx)
instead. If you are using SSL but CLAM does not detect it, you can set
``ASSUMESSL = True``. In this case HTTP Basic Authentication will be the
default authentication mechanism since CLAM 2.2, but HTTP Digest
Authentication is accepted too. If you’re not on an SSL connection, CLAM
will default to HTTP Digest Authentication only and disallow HTTP Basic
Authentication. You can tweak the accepted authentication types by setting the booleans ``BASICAUTH`` and
``DIGESTAUTH``, respectively.

User authentication is not mandatory, but for any world-accessible
environment it is most strongly recommended, for obvious security
reasons.

A list of user accounts and passwords can be defined in ``USERS`` in the
service configuration file itself. This is a simple method allowing you
to quickly define users, but it is not a very scalable method. The
``USERS`` variable is a dictionary of usernames mapped to an md5 hash
computed on the basis of the username, a string representing the
security realm (by default the system ID), and the password. Projects
will only be accessible and visible to their owners, unless no
authentication is used at all, in which case everybody can see all
projects. An example of a configuration with plain text password,
converted on the fly to hashes, is found below:

.. code-block:: python

       USERS = {
           'bob': pwhash('bob', SYSTEM_ID, 'secret'),
           'alice': pwhash('alice', SYSTEM_ID, 'secret2'),
       }

However, computing hashes on the fly like in the above example is quite
insecure and not recommended. You should pre-compute the hashes and add
these instead:

.. code-block:: python

       USERS = {
           'bob': '6d72b6376858cf3c618c826fab1b0109',
           'alice': 'e445370f57e19a8bfa454404ba3892cc',
       }

This pre-computation can be done in an interactive python session,
executed from the CLAM directory. Make sure to change ``yourconfig`` in
the example below to your actual service configuration file:

.. code-block:: python

   from clam.common.digestauth import pwhash
   import clam.config.yourconfig as settings
   pwhash('alice', settings.SYSTEM_ID, 'secret')
   'e445370f57e19a8bfa454404ba3892cc'

You can mark certain users as being administrators using the ``ADMINS``
list. Administrators can see and modify all projects.

The ability to view and set parameters can be restricted to certain users. You can use the extra parameter options
``allowusers=`` or ``denyusers=`` to set this. See the documentation on :ref:`parameters`. A
common use would be to define one user to be the guest user, for instance the user named “guest”, and set
``denyusers=[’guest’]`` on the parameters you do not want the guest user to use.

In production environments, you will also want to set ``SECRET_KEY`` to
a string value that is kept strictly private. It is used for
cryptographically signing session data and preventing CSRF attacks (`details <http://flask.pocoo.org/docs/0.10/quickstart/#sessions>`_).

.. [Franks1999] J. Franks, P. Hallam-Baker, J. Hostelter, S. Lawrence, P.Leach, A. Luotonen and L. Stewart (1999). HTTP Authentication: Basic and Digest Access Authentication (RFC2617). The Internet Engineering Task Force (IETF). `(HTML) <http://tools.ietf.org/html/rfc2617>`_

.. [Hardt2012] D. Hardt (2012) The OAuth 2.0 Authorization Framework (RFC6749). `(Text) <http://www.rfc-editor.org/rfc/rfc6749.txt`_

MySQL backend
~~~~~~~~~~~~~~~~~~~~~

Rather than using ``USERS`` to define a user database in your service
configuration file, a more sophisticated method is available using
MySQL. The configuration variable ``USERS_MYSQL`` can be configured,
instead of ``USERS``, to point to a table in a MySQL database somewhere;
the fields “username” and “password” in this table will subsequently be
used to authenticate against. Custom field names are also possible. This
approach allows you to use existing MySQL-based user databases. The
password field is again a hashed password in the same fashion as in
``USERS``, so it never contains a plaintext password. ``USERS_MYSQL`` is
set as a Python dictionary with the following configurable keys:

.. code-block:: python

       USERS_MYSQL = {
           'host': 'localhost',  #(default)
           'user': 'mysql_user',
           'password': 'secret_mysql_password',
           'database': 'clamopener',
           'table': 'clamusers_clamusers',
           'userfield': 'username',      #(default)
           'passwordfield': 'password',  #(default)
       }

External forwarded authentication schemes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Authentication may also be provided on a more global webserver level,
rather than in CLAM itself. An external layer takes care of the
authentication and forwards a header to the actual application, i.e.
CLAM. This is a feature for advanced service providers wanting to use
external authentication schemes, such as federated identity solutions.
IN CLAM this is implemented using the ``PREAUTHHEADER`` configuration
directive, the value of which is a string containing the name of an HTTP
header which CLAM reads to obtain the authenticated username. This
should be set by an authentication system *prior* to passing control to
CLAM. An example of such a system is Shibboleth  [4]_. Multiple headers
may be specified in ``PREAUTHHEADER``, using space as delimiter,
effectively creating a fallback chain. If the header is not passed
(which should never happen with properly configured middleware), a HTTP
401 reply will be returned.

When such a forwarded authentication scheme is used, proper care has to
be taken, by the middle layer, to ensure that the HTTP headers cannot be
forged by end users themselves!

It is possible that usernames that come from external pre-authentication
methods are different from those in the internal ``USERS`` map (if used
at all), an explicit mapping between the two may be specified in the
``PREAUTHMAPPING`` dictionary.

The example below shows an Apache configuration for a *proxy server* or
*entry server* that forwards to another server on which a CLAM service
runs, mediated through Shibboleth:

::

      <Location /yourclamservice>
           AuthType shibboleth
           ShibRequireSession On
           ShibUseHeaders On
           require valid-user
           ProxyPass http://realserver/yourclamservice
           ProxyPassReverse http://realserver/yourclamservice
      </Location>

The actual server, if it runs Apache, must always contain the
  directive ``WSGIPassAuthorization On``.

The CLAM service configuration file can in turn be restricted to accept
*only* Shibboleth authenticated users by setting ``PREAUTHONLY`` to
``True``, as shown here:

::

   PREAUTHHEADER = 'HTTP_EDUPERSONPRINCIPALNAME'
   PREAUTHONLY = True

Replace ``HTTP_EDUPERSONPRINCIPALNAME`` with the proper HTTP header;
this variable name is just an example in a CLARIN-NL context.

OAuth2
~~~~~~~~~

CLAM also implements OAuth2 [Hardt2012]_, i.e. it acts as
a client in the OAuth2 Authorization framework. An external OAuth2
authorization provider is responsible for authenticating you, using your
user credentials to which CLAM itself will never have access. Many
OAuth2 providers exists; such as Google, Facebook and Github, but you
most likely want to use the OAuth2 provider of your own institution. You
will need to register your webservice with your authentication provider,
and obtain a ``CLIENT_ID`` and ``CLIENT_SECRET``, the latter should be
kept strictly private! These go into your service configuration file and
we then enable OAuth as follows:

.. code-block:: python

   OAUTH = True
   OAUTH_CLIENT_ID = "some_client_id"
   OAUTH_CLIENT_SECRET = "donotsharewithanyone"
   OAUTH_CLIENT_URL = "https://yourwebservice"

Your authorization provider will also ask your for a redirect URL, use the ``/login`` endpoint of your CLAM webservice there
(without trailing slash). ``OAUTH_CLIENT_URL`` is the full URL to your webservice as it is also known to the authorization
provider (minus the redirect endpoint).

Note that OAuth2 by definition requires HTTPS, therefore, it can not be
used with the built-in webserver but requires being embedded in a
webserver such as Apache2, with SSL support.

When the user approaches the CLAM webservice, he/she will need to pass a
valid access token. If none is passed, the user is instantly delegated (HTTP 303)
to the OAuth2 authorization provider. The authorization provider
makes available a URL for authentication and for obtaining the final
access token. These are configured as follows in the CLAM service
configuration file:

.. code-block:: python

   OAUTH_AUTH_URL = "https://yourprovider/oauth/authenticate"
   OAUTH_TOKEN_URL = "https://yourprovider/oauth/token"

The authorization provider in turn redirects the user back to the CLAM
webservice, which in turn returns the access token to the client in its
XML response as follows. Note that there will just be this one tag
without any children.

.. code-block:: xml

   <clam xmlns:xlink="http://www.w3.org/1999/xlink" version="$version"
   id="yourservice"
    name="yourservice" baseurl="https://yourservice.com/"
    oauth_access_token="1234567890">
   </clam>

Now any subsequent call to CLAM must pass this access token, otherwise
you’d simply be redirected to authenticate again. The client must thus
explicitly call CLAM again. Passing the access token can be done in two
ways, the recommended way is by sending the following HTTP header in
your request, where the number is replaced with the actual access token:

::

   Authentication: Bearer 1234567890

The alternative way is by passing it along with the HTTP GET/POST
request. This is considered less secure as your browser may log it in
its history, and the server in its access logs. It can still not be
intercepted by anyone in the middle, however, as it is transmitted over
HTTPS.

::

   https://yourservice.com/?oauth_access_token=1234567890

Automated clients can avoid this method, but it is necessarily used by
the web-based interface. To mitigage security concerns, the access token
you receive is encrypted by CLAM and bound to your IP. The passphrase
for token encryption has to be configured through
``OAUTH_ENCRYPTIONSECRET`` in your service configuration file. The web
interface will furthermore explicitly ask users to log out. Logging out
is done by revoking the access token with the authorization provider.
For this to work, your authentication provider must offer a revoke URL,
as described in `RFC7009 <https://tools.ietf.org/html/rfc7009>`_, which you configure in your service
configuration file as follows:

.. code-block:: python

   OAUTH_REVOKE_URL = "https://yourprovider/oauth/revoke"

If none is set, CLAM’s logout procedure will simply instruct users to
clear their browser history and cache, which is clearly sub-optimal.

The only information CLAM needs from the authorization provider is a
username, or often the email address that acts as a username.
To be able to get the username, a so-called ``userinfo`` end-point is required.

.. code-block:: python

   OAUTH_USERINFO_URL = "https://yourprovider/oauth/userinfo"

CLAM will make some educated guesses to extract the necessary information and will have a preference for using the
e-mail address as a username. If you want something more customised, you can set ``OAUTH_USERNAME_FUNCTION`` and refer it to a (Python)
function that obtains this from your resource provider after you have
been authenticated. It gets a single argument, the ``oauthsession``
instance, and returns the username as a string. The following example
shows how to implement this function for a resource provider that
returns the username in JSON format. This, however, is completely
provider-specific so you always have to write your own function!

.. code-block:: python

   def myprovider_username_function(oauthsession):
     r = oauthsession.get(oauthsession.USERINFO_URL)
     d = json.loads(r.content)
     return d['username']

   OAUTH_USERNAME_FUNCTION = myprovider_username_function

Various providers require the system to specify scopes, indicating the
permissions the application requests from the resource provider. This
can be done using the ``OAUTH_SCOPE`` directive in the service
configuration file, which takes a list of scopes, all of which are
provider-specific. The following example refers to the Google API:

.. code-block:: python

   OAUTH_SCOPE = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
   ]


If you want to use OpenID Connect, a recommended extension on top of OAuth2, you need specify the following scopes:

.. code-block:: python

   OAUTH_SCOPE = [
        "openid",
        "email"
   ]

One of the problems with OAuth2 for automated clients is the
authentication step that often requires user intervention. CLAM
redirects unauthenticated users to the authorization provider. This is
generally a website where the user enters his username and password, but
the means by which authentication proceeds is not fixed by the OAuth2
specification. After authentication, the site passes a one-time
authorization code back to the user, with which the user goes to CLAM to
obtain the actual access token. This access token may be used for a
longer time, depending on the authorization provider.

This implies that automated clients accessing the CLAM service can not
authenticate in a generic fashion that is equal accross authorization
providers, there is again a provider-specific component here and CLAM
clients need to know how to communicate with the specific authorization
provider.

At the moment, CLAM does not yet implement support for refresh tokens.

The unencrypted access token may be passed to the wrapper script if
needed (has to be explicitly configured), allowing the wrapper script or
underlying system to communicate with a resource provider on behalf of
the user, through CLAM’s client_id.


.. _command:

Command Definition
------------------------

Central in the configuration file is the command that CLAM will execute.
This command should start the actual NLP application, or preferably a
script wrapped around it. Full shell syntax is supported. In addition
there are some special variables you can use that will be automatically
set by CLAM.

-  ``$INPUTDIRECTORY`` – The absolute path to the input directory where
   all the input files from the user will be stored (possibly in
   subdirectories). This input directory is the ``input/`` subdirectory
   in the project directory.

-  ``$OUTPUTDIRECTORY`` – The absolute path to the output directory.
   Your system should output all of its files here, as otherwise they
   are not accessible through CLAM. This output directory is the
   ``output/`` subdirectory in the project directory.

-  ``$TMPDIRECTORY`` – The absolute path to the a temporary directory.
   The contents of the directory will be automatically cleared as soon
   as your wrapper script terminates. Your system should output all of
   its temporary files here. This temporary directory is the ``tmp/``
   subdirectory in the project directory.

-  ``$STATUSFILE`` – The absolute path to a status file. Your system may
   write a short message to this status file, indicating the current
   status. This message will be displayed to the user in CLAM’s
   interface. The status file contains a full log of all status
   messages, thus your system should write to this file in append mode.
   Each status message consists of one line terminated by a newline
   character. The line may contain three tab delimited elements that
   will be automatically detected: a percentage indicating the progress
   until completion (two digits with a % sign), a Unix timestamp (a long
   number), and the status message itself (a UTF-8 string).

-  ``$PARAMETERS`` – This variable will contain all parameter flags and
   the parameter values that have been selected by the user. It is
   recommendedm however, to use $DATAFILE instead of $PARAMETERS.

-  ``$DATAFILE`` – The absolute path to the data file that CLAM outputs
   in the project directory. This data file, in CLAM XML format,
   contains all parameters along with their selected values. Furthermore
   it contains the inputformats and outputformats, and a listing of
   uploaded input files and/or pre-installed corpora. System wrapper
   scripts can read this file to obtain all necessary information, and
   as such this method is preferred over using $PARAMETERS. If the
   system wrapper script is written in Python, the CLAM Data API can be
   used to read this file, requiring little effort on the part of the
   developer.

-  ``$USERNAME`` – The username of the logged-in user.

-  ``$PROJECT`` – The ID of the project

-  ``$OAUTH_ACCESS_TOKEN`` – The unencrypted OAuth access token [7]_.

Make sure the actual command is an absolute path, or that the executable
is in the ``$PATH`` of the user ``clamservice`` will run as. Upon
launch, the current working directory will be automatically set to the
specific project directory. Within this directory, there will be an
``input/`` and ``output/`` directory, but use the full path as stored in
``$INPUTDIRECTORY``/ and ``$OUTPUTDIRECTORY``/. All uploaded user input
will be in this input directory, and all output that users should be
able to view or download, should be in this output directory. Your
wrapper script and NLP tool are of course free to use any other
locations on the filesystem for whatever other purposes.

.. _project:

Project Paradigm: Metadata, Profiles & Parameters
-----------------------------------------------------

In order to explain how to build service configuration files for the
tools you want to make into webservices, we first need to clarify the
project paradigm CLAM uses. We shall start with a word about metadata.
Metadata is data *about* your data, i.e. data about your input and
output files. Take the example of a plain text file: metadata for such a
file can be for example the character encoding the text is in, and the
language the text is written in. Such data is not necessarily encoded
within the file itself, as is also not the case in the example of plain
text files. CLAM therefore builds external metadata files for each input
and output file. These files contain all metadata of the files they
describe. These are stored in the CLAM Metadata XML format, a very
simple and straightforward format.  Metadata simply consists of
metadata fields and associated values.

Metadata in CLAM is tied to a particular file format (such as plain text
format, CSV format, etc.). A format defines what kind of metadata it
absolutely needs, but usually still offers a lot of freedom for extra
metadata fields to the service provider, or even to the end user.

When a user or automated client uploads a new input file, metadata is
often not available yet. The user or client is therefore asked to
provide this. In the webapplication a form is presented with all
possible metadata parameters; the system will take care of generating
the metadata files according to the choices made. If the service
provider does not want to make use of any metadata description at all,
then that is of course an option as well, though this may come at the
cost of your service not providing enough information to interact with
others.

In a webservice it is important to define precisely what kind of input
goes in, and what kind of output goes out: this results in a
deterministic and thus predictable webservice. It is also necessary to
define exactly how the output metadata is based on the input metadata,
if that is the case. These definitions are made in so-called *profiles*.
A profile defines *input templates* and *output templates*. The input
templates and output template can be seen as “slots” for certain
filetypes and metadata. An analogy from childhood memory may facilitate
understanding this, as shown and explained in the figure below:

.. figure:: blokkendoos.jpg
   :alt: Box and blocks analogy from childhood memory: the holes on one
   end correspond to input templates, the holes on the other end
   correspond to output templates. Imagine blocks going in through one
   and out through the other. The blocks themselves correspond to input
   or output files *with attached metadata*. Profiles describe how one
   or more input blocks are transformed into output blocks, which may
   differ in type and number. Granted, I am stretching the analogy here;
   your childhood toy did not have this magic feature of course!
   :name: fig:blokkendoos
   :width: 100mm

   Box and blocks analogy from childhood memory: the holes on one end
   correspond to input templates, the holes on the other end correspond
   to output templates. Imagine blocks going in through one and out
   through the other. The blocks themselves correspond to input or
   output files *with attached metadata*. Profiles describe how one or
   more input blocks are transformed into output blocks, which may
   differ in type and number. Granted, I am stretching the analogy here;
   your childhood toy did not have this magic feature of course!

A profile is thus a precise specification of what output files will be
produced given particular input files, and it specifies exactly how the
metadata for the outputfiles can be constructed given the metadata of
the inputfiles. The generation of metadata for output files is fully
handled by CLAM, outside of your wrapper script and NLP application.

Input templates are specified in part as a collection of parameters for
which the user/client is expected to choose a value in the predetermined
range. Output templates are specified as a collection of “metafields”,
which simply assign a value, unassign a value, or copy a value from an
input template or from a global parameter. Through these templates, the
actual metadata can be constructed. Input templates and output templates
always have a label describing their function. Upon input, this provides
the means for the user to recognise and select the desired input
template, and upon output, it allows the user to easily recognise the
type of output file. How all this is specified exactly will be
demonstrated in detail later.

In addition to input files and the associated metadata parameters, there
is another source of data input: global parameters. A webservice may
define a set of parameters that it takes. We will start by explaining
this part in the next section.

.. _parameters:

Parameter Specification
---------------------------

The global parameters which an NLP application, or rather the wrapper
script, can take, are defined in the service configuration file. These
parameters can be subdivided into parameter groups, but these serve only
presentational purposes.

There are seven parameter types available, though custom types can be
easily added. Each parameter type is a Python class taking the
following mandatory arguments:

#. **id** – An id for internal use only.

#. **name** – The name of this parameter; this will be shown to the
   user in the interface.

#. **description** – A description of this parameter, meant for the
   end-user.

The seven parameter types are:

-  :class:`BooleanParameter` – A parameter that can only be turned on or
   off, represented in the interface by a checkbox. If it is turned on,
   the parameter flag is included in ``$PARAMETERS``, if it is turned
   off, it is not. If ``reverse=True`` is set, it will do the inverse.

-  :class:`IntegerParameter` – A parameter expecting an integer number.
   Use ``minrange=``, and ``maxrange=`` to restrict the range if
   desired.

-  :class:`FloatParameter` – A parameter expecting a float number. Use
   ``minrange=``, and ``maxrange=`` to restrict the range if desired.

-  :class:`StringParameter` – A parameter taking a string value. Use
   ``maxlength=`` if you want to restrict the maximum length.

-  :class:`TextParameter` – A parameter taking multiple lines of text.

-  :class:`ChoiceParameter` – A multiple-choice parameter. The choices
     must be specified as a list of ``(ID, label)`` tuples, in which ID
     is the internal value, and label the text the user sees. For
     example, suppose a parameter with flag ``-c`` is defined.
     ``choices=[(’r’,’red’),(’g’,’green’),(’b’, ’blue)]``, and the user
     selects “green”, then ``-c g`` will be added to ``$PARAMETERS``. The default choice can be set with ``default=``,
     and then the ID of the choice. If you want the user to be able to
     select multiple parameters, you can set the option ``multi=True``.
     The IDs will be concatenated together in the parameter value. A
     delimiter (a comma by default) can be specified with
     ``delimiter=``. If you do not use ``multi=True``, but you do want
     all options to be visible in one view, you can set the option
     ``showall=True``.

-  :class:`StaticParameter` – A parameter with a fixed immutable value.
   This may seem a bit of a contradiction, but it serves a purpose in
   forcing a global parameter or metadata parameter to have a specific
   non-variable value.

All parameters can take the following extra keyword arguments:

-  **paramflag** – The parameter flag. This flag will be added to
   ``$PARAMETERS`` when the parameter is set. Consequently, it is
   mandatory if you use the ``$PARAMETERS`` variable in your ``COMMAND``
   definition. It is customary for parameter flags to consist of a
   hyphen and a letter or two hyphens and a string. Parameter flags
   could for example be formed like: ``-p`` ,\ ``–pages``, ``–pages=``.
   There will be a space between the parameter flag and its value,
   unless it ends in a ``=`` sign or ``nospace=True`` is set. Multi-word
   string values will automatically be enclosed in quotation marks for
   the shell to correctly parse them. Technically, you are also allowed
   to specify an empty parameter flag, in which case only the value will
   be outputted as if it were an argument.

-  **default** – Set a default value.

-  **required** – Set to ``True`` to make this parameter required
   rather than optional.

-  **require** – Set this to a list of parameter IDs. If this
   parameter is set, so must all others in this list. If not, an error
   will be returned.

-  **forbid** – Set this to a list of parameter IDs. If this
   parameter is set, none of the others in the list may be set. If not,
   an error will be returned.

-  **allowusers** – Allow only the specified lists of usernames to
   see and set this parameter. If unset, all users will have access. You
   can decide whether to use this option or ``denyusers``, or to allow
   access for all.

-  **denyusers** – Disallow the specified lists of usernames to see
   and set this parameter. If unset, no users are blocked from having
   access. You can decide whether to use this option or ``allowusers``,
   or to allow access for all.

-  **validator** – This should be a Python function (or other
   callable) taking one argument (the parameter’s value), and returning
   either boolean indication whether the value is valid, or a (boolean,
   errormsg) tuple.

The following example defines a boolean parameter with a parameter flag:

.. code-block:: python

   BooleanParameter(
     id='createlexicon',
     name='Create Lexicon',
     description='Generate a separate overall lexicon?',
     paramflag='-l'
   )

Thus, if this parameter is set, the invoked command will have
``$PARAMETERS`` set to ``-l 1`` (plus any additional parameters).

Parameters API
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: clam.common.parameters
    :members:
    :undoc-members:

.. _profile:

Profile specification
---------------------------

Multiple profiles may be specified, and all profiles are always assumed
to be independent of each other. Dependencies should be together in one
profile, as each profile describes how a certain type of input file is
transformed into a certain type of output file. For each profile, you
need to define input templates and output templates. All matching
profiles are assumed to be delivered as promised. A profile matches if
all input files according to the input templates of that profile are
provided and if it generates output. If no input templates have been
defined at all for a profile, then it will match as well, to allow for
the option of producing output files that are not dependent on input
files. A profile is allowed to mismatch, but if none of the profiles
match, the system will produce an error, as it cannot perform any
actions.

The profile specification skeleton looks as follows. Note that there may
be multiple input templates and/or multiple output templates:

.. code-block:: python

   PROFILES = [
       Profile( InputTemplate(...), OutputTemplate(...) )
   ]

The definition for :class:`InputTemplate` takes three mandatory arguments:

#. ``id`` – An ID for the InputTemplate. This will be used internally
   and by automated clients.

#. ``format`` – This points to a Format class, indicating the kind of
   format that this input template accepts. Formats are defined in
   ``clam/common/formats.py``. Custom formats can be added there. Custom
   format classes can also be defined in the service configuration
   itself, after which you need to add these classes to the
   ``CUSTOM_FORMATS`` list.

#. ``label`` – A human readable label for the input template. This is
   how it will be known to users in the web application and displayed in
   its selection menus.

After the three mandatory arguments, you may specify any of the Parameter types to indicate the accepted/required
metadata for the particular input templates. Use any of the parameter types (see :ref:`parameters`) .  We will come to an
example of this soon.

After specifying any such parameters, there are some possible keyword
arguments:

#. ``unique`` – Set to ``True`` or ``False``; this indicates whether the
   input template may be used only once or multiple times.
   ``unique=True`` is the default if not specified.

#. ``multi`` – The logical inverse of the above; you can whichever you
   prefer. ``multi=False`` is the default if not specified.

#. ``filename`` – Files uploaded through this input template will
   receive this filename (regardless of how the original file on the
   client is called). If you set ``multi=True`` or its alias
   ``unique=False``, insert the variable ``$SEQNR`` into the filename,
   which will be replaced by a number in sequence. After all, we cannot
   have multiple files with the same name. As explained in
   :ref:`filenamevariables`, you can also use any of
   the metadata parameters as variable in the filename.

#. ``extension`` – Files uploaded through this input template are
   expected to have this extension, but can have any filename. Here it
   does not matter whether you specify the extension with or without the
   prefixing period. Note that in the web application, the extension is
   appended automatically regardless of the filename of the source file.
   Automated clients do must take care to submit files with the proper
   extension right away.

#. ``acceptarchive`` – This is a boolean which can be set to True if you
   want to accept the upload of archives. Uploaded archives will be
   automatically unpacked. It is a method to instantly upload multiple
   files *for the same input template*. The file must be in zip, tar.gz
   or tar.bz2 format. The files within the archive will be renamed
   according to the input template’s specifications if necessary. Using
   this option implies that the exact same metadata will be associated
   with all uploaded files! This option can only be used in combination
   with ``multi=True``. Note that archives can only be uploaded when all
   files therein fit the same input template!

Take a look at the following example of an input template for plaintext
documents for an automatic translation system, illustrating of all the
above:

.. code-block:: python

   InputTemplate('maininput', PlainTextFormat,
     "Translator input: Plain-text document",
     StaticParameter(
       id='encoding',name='Encoding',
       description='The character encoding of the file',
       value='utf-8'
     ),
     ChoiceParameter(
       id='language',name='Language',
       description='The language the text is in',
       choices=[('en','English'),('nl','Dutch'),('fr','French')]),
     ),
     extension='.txt',
     multi=True
   )

For :class:`OutputTemplate`, the syntax is similar. It takes the three
mandatory arguments *id*, *format* and *label*, and it also takes the
four keyword arguments laid out above. If no explicit filename has been
specified for an output template, then it needs to find out what name
the output filename will get from another source. This other source is
the input template that acts as the *parent*. The output template will
thus inherit the filename from the input template that is its parent. In
this way, the user may upload a particular file, and get that very same
file back with the same name. If you specify ``extension``, it will
append an extra extension to this inherited filename. Prior to appending
an extension, you may often want to remove an existing extension; you
can do that with the ``removeextension`` attribute. As there may be
multiple input templates, it is not always clear what input template is
the parent. The system will automatically select the *first* defined
input template with the same value for unique/multi the output template
has. If this is not what you want, you can explicitly set a parent using
the ``parent`` keyword, which takes the value of the input template’s
ID.

Whereas for :class:`InputTemplate` you can specify various parameter types,
output templates work differently. Output templates define what metadata
fields (metafields for short) they want to set with what values, and
from where to get these values. In some situations the output file is an
extension of the input file, and you want it to inherit the metadata
from the input file. Set ``copymetadata=True`` to accomplish this: now
all metadata will be inherited from the parent, but you can still make
modifications.

To set (or unset) particular metadata fields you specify so-called
“metafield actors”. Each metafield actor sets or unsets a particular
metadata attribute. There are four different types of metafield actors:

-  :class:`SetMetaField` ``(key,value)`` – Set metafield *key* to the specified
   value.

-  :class:`UnsetMetaField` ``(key[,value])`` – If a value is specified: Unset
     this metafield if it has the specified value. If no value is
     specified: Unset the metafield regardless of value. This only makes
     sense if you set ``copymetadata=True``.

-  :class:`CopyMetaField` ``(key, inputtemplate.key)`` – Copy metadata from one of
   the input template’s metadata. Here *inputtemplate* is the ID of one
   of the input templates in the profile, and the *key* part is the
   metadata field to copy. This allows you to combine metadata from
   multiple input sources into your output metadata.

-  :class:`ParameterMetaField` ``(key, parameter-id)`` – Get the value for this
   metadata field from a global parameter with the specified ID.

Take a look at the following example for a fictitious automatic
translation system, translating to Esperanto. If an input file ``x.txt``
is uploaded, the output file will be named ``x.translation``.

.. code-block:: python

   OutputTemplate('translationoutput', PlainTextFormat,
       "Translator output: Plain-text document",
       CopyMetaField('encoding','maininput.encoding')
       SetMetaField('language','eo'),
       removeextension='.txt',
       extension='.translation',
       multi=True
   )

Putting it all together, we obtain the following profile definition
describing a fictitious machine translation system from English, Dutch
or French to Esperanto, where the system accepts and produces UTF-8
encoded plain-text files.

.. code-block:: python

   PROFILES = [
     Profile(
       InputTemplate('maininput', PlainTextFormat,
        "Translator input (Plain-text document)",
         StaticParameter(
          id='encoding',name='Encoding',
          description='The character encoding of the file',
          value='utf-8'
         ),
         ChoiceParameter(
          id='language',name='Language',
          description='The language the text is in',
          choices=[('en','English'),('nl','Dutch'),('fr','French')]
         ),
         extension='.txt',
         multi=True
       ),
       OutputTemplate('translationoutput', PlainTextFormat,
         "Esperanto translation (Plain-text document)",
         CopyMetaField('encoding','maininput.encoding')
         SetMetaField('language','eo'),
         removeextension='.txt',
         extension='.translation',
         multi=True
       )
     )
   ]

.. _filenamevariables:

Control over filenames
~~~~~~~~~~~~~~~~~~~~~~~

There are several ways of controlling the way input and output files
within a profile are named. As illustrated in the previous section, each
output template has an input template as its parent, from which it
inherits the filename if no explicit filename is specified. This is a
very important aspect that has to be considered when building your
profiles. By default, if no ``filename=``, ``extension=`` or
``removeextension=`` is specified for an output template, it will use
the same filename as the parent input template. If ``filename=`` and
``extension=`` are not specified for the Input Template, then the file
the user uploads will simply maintain the very same name as it is
uploaded with. If ``extension=`` is specified, the input file is
required to have the specified extension, the web application and CLAM
Client API takes care of this automatically if this is not the case.

In a previous section, we mentioned the use of the variable ``$SEQNR``
that will insert a number in the filename when the input template or
output template is in multi-mode. In addition to this, other variables
can also be used. Here is an overview:

-  ``$SEQNR`` - The sequence number of the file. Valid only if
   ``unique=True`` or ``multi=False``.

-  ``$PROJECT`` - The ID of the project.

-  ``$INPUTFILENAME`` - The filename of the associated input file. Valid
   only in Output Templates.

-  ``$INPUTSTRIPPEDFILENAME`` - The filename of the associated input
   file without any extensions. Valid only in Output Templates.

-  ``$INPUTEXTENSION`` - The extension of the associated input file
   (without the initial period). Valid only in Output Templates.

Other than these pre-defined variables by CLAM, you can use any of the
metadata parameters as variables in the filename, for input templates
only. To this end, use a dollar sign followed by the ID of the parameter
in the filename specification. For Output Templates, you can use
metafield IDs or global parameter IDs (in that order of priority) in the
same way. This syntax is valid in both ``filename=`` and ``extension=``.

The following example illustrates a translation system that encodes the
character encoding and language in the filename itself. Note also the
use of the special variable ``$SEQNR``, which assigns a sequence number
as the templates are both in multi mode.

.. code-block:: python

   PROFILES = [
     Profile(
       InputTemplate('maininput', PlainTextFormat,
         "Translator input (Plain-text document)",
         StaticParameter(
          id='encoding',name='Encoding',
          description='The character encoding of the file',
          value='utf-8'
         ),
         ChoiceParameter(
          id='language',name='Language',
          description='The language the text is in',
          choices=[('en','English'),('nl','Dutch'),('fr','French')]
         ),
         filename='input$SEQNR.$language.$encoding.txt'
         multi=True
       ),
       OutputTemplate('translationoutput', PlainTextFormat,
         "Esperanto translation (Plain-text document)",
         CopyMetaField('encoding','maininput.encoding')
         SetMetaField('language','eo'),
         filename='output$SEQNR.$language.$encoding.txt'
         multi=True
       )
     )
   ]

In addition to variables that refer to global or local parameters. There
are some additional variables set by CLAM which you can use:

-  ``$PROJECT`` - Is set to the project ID.

-  ``$INPUTFILE`` - Is set to the project ID.

.. _paramcond:

Parameter Conditions
~~~~~~~~~~~~~~~~~~~~

It is not always possible to define all output templates straight away.
Sometimes output templates are dependent on certain global parameters.
For example, given a global parameter that toggles the generation of a
lexicon, you want to include only the output template that describes
this lexicon, if the parameter is enabled. CLAM offers a solution for
such situations using the :class:`ParameterCondition` directive.

Assume you have the following *global* parameter:

.. code-block:: python

   BooleanParameter(
     id='createlexicon',name='Create Lexicon',
     description='Create lexicon files',
   )

We can then turn an output template into an output template conditional
on this parameter using the following construction:

.. code-block:: python

     ParameterCondition(createlexicon=True,
       then=OutputTemplate('lexiconoutput', PlainTextFormat,
         "Lexicon (Plain-text document)",
         unique=True
       )
     )

The first argument of :class:`ParameterCondition` is the condition. Here you use
the ID of the parameter and the value you want to check against. The
above example illustrates an equality comparison, but other comparisons
are also possible. We list them all here:

-  ``ID=value`` – Equality; matches if the global parameter with the
   specified ID has the specified value.

-  ``ID_equals=value`` – Same as above, the above is an alias.

-  ``ID_notequals=value`` – The reverse of the above, matches if the
   value is *not equal*

-  ``ID_lessthan=number`` – Matches if the parameter with the specified
   ID is less than the specified number

-  ``ID_greaterthan=number`` – Matches if the parameter with the
   specified ID is greater tha then specified number

-  ``ID_lessequalthan=number`` – Matches if the parameter with the
   specified ID is equal or less than the specified number

-  ``ID_greaterequalthan=number`` – Matches if the parameter with the
   specified ID is equal or greater than the specified number

After the condition you specify ``then=`` and optionally also ``else=``,
and then you specify an :class:`OutputTemplate` or yet another
:class:`ParameterCondition` — they can be nested at will.

Parameter conditions cannot only be used for output templates, but also
for metafield actors, inside the output template specification. In other
words, you can make metadata fields conditional on global parameters.

Parameter conditions cannot be used for input templates, for the simple
reason that in CLAM the parameters are set after the input files are
uploaded. However, input templates can be *optional*, by setting
``optional=True``. This means that providing such input files is
optional. This also implies that any output templates that have this
optional input template as a parent are also conditional on the presence
of those input files.

Converters
~~~~~~~~~~

Users do not always have their files in the format you desire as input,
and asking users to convert their data may be problematic. Similarly,
users may not always like the output format you offer. CLAM therefore
introduces a converter framework that can do two things:

#. Convert input files from auxiliary formats to your desired format,
   upon upload;

#. Convert output files from your output format to auxiliary formats.

A converter, using the above-mentioned class names, can be included in
input templates (for situation 1), and in output templates (for
situation 2). Include them directly after any Parameter fields or
Metafield actors.

It is important to note that the converters convert only the files
themselves and not the associated metadata. This implies that these
converters are intended primarily for end users and not as much for
automated clients.

For most purposes, you will need to write your own converters. These are
to be implemented in ``clam/common/converters.py`` and derived off :class:`AbstractConverter`. Some converters
however will be provided out of the box. Note that the actual conversion
will be performed by 3rd party software in most cases.

-  ``MSWordConverter`` – Convert MS Word files to plain text. This
   converter uses the external tool `catdoc <http://www.wagner.pp.ru/~vitus/software/catdoc/>`_ by default and will only
   work if installed.

-  ``PDFConverter`` – Convert PDF to plain text. This converter uses the
   external tool `pdftohtml <http://pdftohtml.sourceforge.net/>`_ by default and will only work if installed.

-  ``CharEncodingConverter`` – Convert between plain text files in
   different character encodings.

Note that specific converters take specific parameters; consult the API
reference for details.

.. _viewers:

Viewers
~~~~~~~

Viewers are intended for human end users, and enable visualisation of a
particular file format. CLAM offers a viewer framework that enables you
to write viewers for your format. Viewers may either be written within
the CLAM framework, using Python, but they can also be external
(non-CLAM) webservices, hosted elsewhere. Several simple viewers for
some formats are provided already; these are defined in ``viewers.py`` and derived off :class:`AbstractViewer`.

Viewers can be included in output templates. Include them directly after any metafield actors. The first viewer you
define will be the default viewer for that particular output template, unless you set ``allowdefault=False`` on the viewer.

The below example illustrates the use of the viewer
``SimpleTableViewer``, capable of showing CSV files:

.. code-block:: python

   OutputTemplate('freqlist',CSVFormat,"Frequency list",
       SimpleTableViewer(),
       SetMetaField('encoding','utf-8'),
       extension='.patterns.csv',
   )

Another useful viewer is the :class:`ForwardViewer`. It forwards the viewing request to a remote service and passes a
backlink where the remote service can *download* the output file without further authentication.  Users are taken
directly to the remote service, that is, their browsers/clients are directly redirected to the specified URL. To have
CLAM itself invoke the URL, you have to set ``indirect=True`` on the Forwarder, in that case CLAM will invoke the remote
URL itself and the remote service is expected to return a HTTP 302 Redirect response which CLAM will subsequently
invoke.

.. code-block:: python

   OutputTemplate('freqlist',CSVFormat,"Frequency list",
       ForwardViewer(
            Forwarder(id="some_remote_service",name="Some Remote Frequency List Viewer"),
                      url="https://remote.service.com/?download=$BACKLINK")),
       SetMetaField('encoding','utf-8'),
       extension='.patterns.csv',
   )

The ``$BACKLINK`` variable will be replaced by CLAM by the actual URL where the resource can be obtained. By default,
this is a one time download link that uses a temporary storage that does not require authentication, circumventing user
delegation problems. This is safe as long as all communication is encrypted, i.e. over HTTPS. If you don't want this
behaviour, pass ``tmpstore=False`` on the Forwarder.

Other variables are also available, such as ``$MIMETYPE``. You can reference any associated parameters using their ID in uppercase, so in this example you would have the variable ``$ENCODING`` available as well. All variables will be url encoded by default, if you don't want this, pass ``encodeurl=False`` to the Forwarder.

You can also use forwarders globally to redirect all output as an archive (zip/tar.gz/tar.bz2), see :ref:`forwarders`.


Viewer API
+++++++++++++++

.. automodule:: clam.common.viewers
    :members:
    :undoc-members:

.. _forwarders:

Forwarders
~~~~~~~~~~~~~~

To allow users to forward all output from one webservice to another, you can use Forwarders. The forwarder calls a
remote service and passes a backlink where the remote service can *download* the output file once, without further
authentication (by default). Users are taken directly to the remote service, that is, their browsers/clients are
directly redirected to the specified URL. To have CLAM itself invoke the URL, you have to set ``indirect=True`` on the
Forwarder, in that case CLAM will invoke the remote URL itself and the remote service is expected to return a HTTP 302
Redirect response which CLAM will subsequently invoke.

.. code-block:: python

    FORWARDERS = [
           Forwarder(id="some_remote_service",name="Some Remote service",type="zip", description="",
            url="https://remote.service.com/?downloadarchive=$BACKLINK"
           )
    ]

The ``$BACKLINK`` variable will be replaced by CLAM by the actual URL where the resource can be obtained. By default,
this is a one time download link that uses a temporary storage that does not require authentication, circumventing user
delegation problems. This is safe as long as all communication is encrypted, i.e. over HTTPS. If you don't want this
behaviour, pass ``tmpstore=False`` on the Forwarder. Other variables are also available, such as ``$MIMETYPE``. All
variables will be url encoded by default, if you don't want this, pass ``encodeurl=False`` to the Forwarder.



.. note::

    * Forwarders can also be used as viewers for individual files. See :ref:`viewers`
    * A forwarder does *NOT* perform any upload, it just passes a download link to a service, the remote.


Input Sources: Working with pre-installed data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rather than letting users upload files, CLAM also offers the possibility
of pre-installing input data on the server. This feature is ideally
suited for dealing with data for a demo, or for offering a selection of
pre-installed corpora that are too big to transfer over a network.
Furthermore, pre-installed data is also suited in situations where you
want the user to be able to choose from several pre-installed resources,
such as lexicons, grammars, etc., instead of having to upload files they
may not have available.

Pre-installed data sources are called “input sources” in CLAM, not to be
confused with input templates. Input sources can be specified either in
an input template, or more globally.

Take a look at the following example:

.. code-block:: python

   InputTemplate('lexicon', PlainTextFormat,"Input Lexicon",
      StaticParameter(id='encoding',name='Encoding',
          description='Character encoding',
          value='utf-8'),
      ChoiceParameter(id='language',name='Language',
          description='The language the text is in',
          choices=[('en','English'),('nl','Dutch'),('fr','French')]),
      InputSource(id='lexiconA', label="Lexicon A",
       path="/path/to/lexiconA.txt",
       metadata=PlainTextFormat(None, encoding='utf-8',language='en')
      ),
      InputSource(id='lexiconB', label="Lexicon B",
       path="/path/to/lexiconB.txt",
       metadata=PlainTextFormat(None, encoding='utf-8',language='en')
      ),
      onlyinputsource=False
   )

This defines an input template for some kind of lexicon, with two
pre-defined input sources: “lexicon A” and “lexicon B”. The user can
choose between these, or alternatively upload a lexicon of his own. If,
however, ``onlyinputsource`` is set to ``True``, then the user is forced
to choose only from the input sources, and cannot upload his own
version.

Metadata can be provided either in the inputsource configuration, or by
simply adding a CLAM metadata file alongside the actual file. For the
file , the metadata file would be (note the initial period; metadata
files are hidden).

Input sources can also be defined globally, and correspond to multiple
files, i.e. they point to a directory containing multiple files instead
of pointing to a single file. Let us take the example of a spelling
correction demo, in which a test set consisting out of many text
documents is the input source:

.. code-block:: python

   INPUTSOURCES = [
       InputSource(id='demotexts', label="Demo texts",
           path="/path/to/demotextdir/",
           metadata=PlainTextFormat(None, encoding='utf-8',
                    language='en'),
           inputtemplate='maininput',
          ),
   ]

In these cases, it is essential to set the ``inputtemplate=`` parameter.
All files in the directory must be formatted according to this input
template. Adding input sources for multiple input templates is done by
simply defining multiple input sources.

Constraints and Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to define additional constraints on input templates, because often it is not enough to know the format
but you need more specific information about it that can be extracted from the file itself. Examples of such information
are dimensions and colour depth for images, bitrate and duration for sound clips.

These constaints are evaluated during validation of the input file, and can only be done if there is a validator
implemented in the format class you are using. Aside from validating the validity of the file, the validator therefore
also has the job to extract metadata from the file itself and make it available to CLAM (including it in the metadata
assembled). Only then, constraints begin to play a role, as you can now constrain on inferred metadata rather than
explicitly supplied input parameters.

To actual keys you can use depends on the attributes defined by the format. Consider the following example which accepts
FoLiA documents but requires that they are at least in version 2.0 or above:

.. code-block:: python

   InputTemplate('inputdoc', FoLiAXMLFormat,"Input Document",
        RequireMeta(version_greaterthan="2.0"),
        extension=".folia.xml"
    )

If you want to add multiple constraints, add multiple ``RequireMeta`` or ``ForbidMeta`` statements. If you specify
multiple keyword arguments, they are treated as a *disjunction*, and the constraint will trigger if any of them test
positively.

The keyword arguments for constraints consist may contain one of the following operators, as indicated by their suffix.
They are analogous to the ones used in Parameter Conditions.

* ``_equals`` (the default one if there is no operator suffix)
* ``_notequals``
* ``_greaterthan``
* ``_greaterequalthan``
* ``_lessthan``
* ``_lessequalthan``
* ``_in`` - Checks if the value is in a list (a list in the pythonic sense)
* ``_incommalist`` - Checkes if the value is in a comma separated string
* ``_inspacelist`` - Checkes if the value is in a space separated string

If you want to implement a validator for your custom format (a subclass of ``CLAMMetaData``), you need to overload and
implement its ``validator()`` method.


Multiple profiles, identical input templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible and sometimes necessary to define more than one profile.
Recall that each profile defines what output will be generated given
what input, and how the metadata is translated. Multiple profiles come
into the picture as soon as you have a disjunction of possible inputs.
Imagine a spelling check system that can take either plain text as
input, or a kind of XML file. In this situation you have two profiles;
one for the plain-text variant, and one for the XML variant.

Now suppose there is another kind of mandatory input, a lexicon against
which spell checking occurs, that is relevant for *both* profiles, and
exactly the same for both profiles. In such circumstances, you could
simply respecify the full input template, with the same ID as in the
other profile. The most elegant solution however, is to instantiate the
input template in a variable, prior to the profile definition, and then
use this variable in both profiles.

Although you can specify multiple profiles, only one profile can match per project run, and there should be no
ambiguity.

.. _custominterface:

Customising the web interface
-----------------------------------

The CLAM web application offers a single uniform interface for all kinds
of services. However, a certain degree of customisation is possible. One
thing you may want is to include more HTML text on the pages, possibly
enriched with images and hyperlinks to external sites. It is an ideal
way to add extra instructions for your users. You may do so using the
following variables in the service configuration file:

-  ``CUSTOMHTML_INDEX`` - This text will be included in the index view,
   the overview of all projects.

-  ``CUSTOMHTML_PROJECTSTART`` - This text will be included in the
   project view where the user can upload files and select parameters.

-  ``CUSTOMHTML_PROJECTDONE`` - This text will be included in the
   project view when the project is done and output is ready to be
   viewed/downloaded.

-  ``CUSTOMHTML_PROJECTFAILED`` - This text will be included in the
   project view when an error occurred while running the project

-  ``CUSTOMCSS`` - This may hold custom CSS styling hat will be applied to the interface.

As the HTML text will be embedded on the fly, take care *not* to include
any headers. Only tags that go within the HTML ``body`` are permitted!
Always use the utf-8 encoding and well-formed xhtml syntax.

The web interface also support a cover image, which is an image at the head of the website. You can specify such an
image in ``SYSTEM_COVER_URL``.

A second kind of customisation is customisation of the style, which can be achieved by creating new CSS themes. CLAM
gets shipped with the default “classic” style (which did receive a significant overhaul in CLAM 0.9 and again with CLAM
3.0). Copy, rename and adapt ``style/classic.css`` to create your own style. And set ``STYLE`` accordingly in your
service configuration file. The ``STYLE`` may also refer to an absolute path of a CSS file to include.

In your service configuration file you can set a variable
``INTERFACEOPTIONS``; this string is a space-separated list in which you
can use the following directives to customise certain aspects of the
web-interface:

-  ``simpleupload`` – Use the simple uploader instead of the more
   advanced javascript-based. The simple uploader does not support
   multiple files but does provide full HTTP Digest Security whereas the
   default and more advanced uploader relies on a less sophisticated
   security mechanism.

-  ``simplepolling`` – Uses a simpler polling mechanism in the stage in
   which CLAM awaits the completion of a process. This method simply
   refreshes the page periodically, while the default method is
   asynchronous but relies on a less sophisticated security mechanism.

-  ``secureonly`` – Equals to ``simpleupload`` and ``simplepolling``,
   forcing only methods that fully support HTTP Digest Authentication.

-  ``disablefileupload`` – Disables the file uploader in the interface
   (do note that this is merely cosmetic and not a security mechanism,
   the RESTful webservice API will continue to support file uploads).

-  ``inputfromweb`` – Enables downloading an input file from the web (do
   note that this is merely cosmetic and not a security mechanism, the
   RESTUL webservice API always supports this regardless of visibility
   in the interface).

-  ``disableliveinput`` – Disables adding input through the live
   in-browser editor.

-  ``preselectinputtemplate`` – Pre-select the first defined input
   template as default inputtemplate, even if there are multiple input templates.

- ``centercover`` - Center the cover image horizontally.

- ``coverheight64``, ``coverheight100``, ``coverheight128``, ``coverheight192`` - Sets the height of the cover imag
  (alternatively you can use the ``CUSTOMCSS`` setting and do it yourself)


.. _actions:

Actions
---------

A simple remote procedure call mechanism is available in addition to the more elaborate project paradigm.

This action paradigm allows you to specify *actions*, each action allows
you to tie a URL to a script (command) or Python function, and may take a number
of parameters you explicitly specify. Each action is strictly
independent of other actions, and completely separate of the projects,
and by extension also of any files within projects and any profiles.
Unlike projects, which may run over a long time period and are suited
for batch processing, actions are intended for real-time communication.
Typically they should return an answer in at most a couple of seconds.

Actions are specified in the service configuration file in the
``ACTIONS`` list. Consider the following example:

.. code-block:: python

   ACTIONS = [
     Action(id='multiply',name="Multiplier",
     description="Multiply two numbers",
     command="/path/to/multiply.sh $PARAMETERS",
     mimetype="text/plain",
     tmpdir=False,
     parameters=[
       IntegerParameter(id='x',name="Value 1"),
       IntegerParameter(id='y',name="Value 2"),
     ])
   ]

The ID of the action determines on what URL it listens. In this case the
URL will be ``/actions/multiply/``, relative to the root of your
service. The name and display are for presentational purposes in the
interface.

Actions will show in the web-application interface on the index page.

In this example, we specify two parameters, they will be passed *in the order
they are defined* to the script. The command to be called is configured
analagous to ``COMMAND``, but only a subset of the variables are supported. The
most prominent is the ``$PARAMETERS`` variable. Note that you can set
``paramflag`` on the parameters to pass them with an option flag. String
parameters with spaces will work without problem (be ware that shells do have a
maximum length for all parameters combined). Actions do not have the notion of
the CLAM XML datafile that wrapper scripts in the project paradigm can use, so
passing command-line parameters is the only way here.

It may, however, not even be necessary to invoke an external script.
Actions support calling Python functions directly. Consider the
following trivial Python function for multiplication:

.. code-block:: python

   def multiply(a,b):
     return a * b

You can define functions in the service configuration file itself, or
import it from elsewhere. We can now use this as an action directly:

.. code-block:: python

   ACTIONS = [
     Action(id='multiply',name="Multiplier",
     description="Multiply two numbers",
     function=multiply,mimetype="text/plain"
     parameters=[
       IntegerParameter(id='x',name="Value 1"),
       IntegerParameter(id='y',name="Value 2"),
     ])
   ]

Again, the parameters are passed in the order they are specified,
irregardless of their names. If you want to pass them as keyword arguments instead you can do so by setting
``parameterstyle="keywords"``. A mismatch in parameters will result in an
error as soon as you try to use the action. All parameters will always
be validated prior to calling the script or function.

When an action completes, the standard output of the script or the
return value [13]_ of the function is returned to the user directly (as
HTTP 200) and as-is. It is therefore important to specify what MIME type
the user can expect, the default is ``text/plain``, but for many
applications ``text/html``, ``text/xml`` or ``application/json`` may be
more appropriate.

Alternatively, you can also associate viewers with an action, just like with output templates. In the interface, a user
may then select one (or none) of those viewers to use for presenting the output.

By default, actions listen to both GET and POST requests. You may
constrain it explicitly by specifying ``method="GET"`` or
``method="POST"``.

When a script is called, CLAM looks at its return code to determine
whether execution was successful (:math:`0`). If not, CLAM will return
the standard error output in a “HTTP 500 – Internal Server Error” reply.
If you define your own errors and return standard *output* in an HTTP
403 reply, use return code :math:`3`; for standard output in an HTTP 404
reply, use return code :math:`4`. These are just defaults, all return
codes are configurable through the keyword arguments ``returncodes200``,
``returncodes403``, ``returncodes404``, each being a list of integers.

When using Python functions, exceptions will be caught and returned to
the end-user in a HTTP 500 reply (without traceback). For custom
replies, Python functions may raise any instance of
``web.webapi.HTTPError``.

If the action invokes a script that outputs temporary files, you may set
``tmpdir=True``, this will create a temporary directory for the duration
of the action, which will be used as current working directory when the
action runs. It will be automatically removed when the action ends. You
may also explicitly pass this directory to the script you invoke with
``command=`` using the ``$TMPDIRECTORY`` variable.

If you enabled an authentication mechanism, as is recommended, it
automatically applies to all actions. It is, however, possible to exempt
certain actions from needing authentication, allowing them to serve any
user anonymously. To do so, add the keyword argument
``allowanonymous=True`` to the configuration of the action.

If you want to use only actions and disable the project paradigm
entirely, set the following in your service configuration file:

.. code-block:: python

   COMMAND = None
   PROFILES = []
   PARAMETERS = []

.. _externalconf:

External Configuration Files
------------------------------

Since CLAM 2.3, you can define part of your webservice configuration in external YAML configuration files. In your
normal service configuration file you then place a call to ``loadconfig(__name__)``. This will automatically search for
external configuration files and includes any variables defined therein just as if they were defined directly. The power
of this mechanism lies in the fact that it allows you to load a different external configuration file for hosts,
allowing you to deploy your CLAM service on multiple hosts without changing the core of the service configuration.

The use of external configuration files is recommend and is also the
default if you create new projects with ``clamnewproject``.

The procedure is as follows, CLAM’s ``loadconfig()`` function will
attempt to search for a file named as follows, in the following order:

-  ``$CONFIGFILE`` - If this environment variable is set, the exact file
   specified therein will be the file to load. This should be an
   absolute path reference rather than just a filename.

-  ``$SYSTEM_ID.$HOSTNAME.yml`` - Here SYSTEM_ID must have been defined
   in the regular service configuration file, prior to calling
   ``loadconfig()``, ``$HOSTNAME`` is the autodetected hostname of the
   system CLAM is running on.

-  ``$SYSTEM_ID.config.yml``

-  ``$HOSTNAME.yml``

-  ``config.yml`` - Note that this filename does not contain any
   variable components, so it’s a final catch-all solution.

CLAM will look in the following directories:

-  The current working directory (so depends on how CLAM was started)

-  The directory where the regular service configuration file exists

An example of a simple external configuration file in YAML syntax is:

::

   root: /var/wwwdata/myservice
   hostname: myhost
   urlprefix: myservice

All field names will be automatically uppercased for CLAM (so
root here becomes ROOT).

A simple form of templating is supported to refer to environment
variables. Enclose the environment variable in double curly braces (no
spaces).

You can define any variable, but the external configuration file is
meant for host-specific configuration only; it can not be used to
specify a full CLAM profile so is never a full substitute for the main
service configuration file.

It is even possible to include other external configuration files from the external configuration itself::

    include: /path/to/other.yml

or multiple::

    include: [ "/path/to/other.yml", "/path/to/other2.yml" ]

External configuration files may refer to standard environment variables by refering to them in curly braces::

   root: "{{ROOT}}"

If the variable does not exist or is empty, it will not be set alltogether. If you want to force a hard error message
instead, add an exclamation mark::

   root: "{{ROOT!}}"

Alternatively, you can specify a default value as follows::

   root: "{{ROOT=/tmp/data}}"

It is also possible to typecast variables using the functions `int`, `bool`, `float` or `json`, this is done using the
pipe character immediately after the variable name (before any of the previously mentioned options)::

   number: "{{NUMBER|int}}"


