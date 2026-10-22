clam(5)

# NAME

clam - Turns command-line applications into RESTful webservice with a web-interface, so both automated client and humans can interact with your tool over the web.

# SYNTAX

A CLAM service is configured via a single configuration file in *TOML* syntax.
See https://toml.io/en/ for generic information about TOML if you are not
familiar with the syntax.

# GENERAL CONFIGURATION

At the root of the configuration, the following fields are available:

*name* (string, mandatory)
	The human-readable name of the webservice
*version* (string, mandatory)
	The version of the webservice, increment this on subsequent releases. Semantic versioning is strongly recommended.
*description* (string)
	Description of the service, supports CommonMark syntax. (for human end-users)
*authors* (list of strings)
	The authors that built the webservice
*email* (string)
	E-mail address for users to contact about this webservice
*affiliation* (string)
	Affiliation/producer/provider for the webservice
*url* (string)
	Base URL where this webservice is served. This is required if you use OpenID Connect authentication. Do not add a trailing slash.
*rootdir* (string)
	Base path on the file system where the user files for the webservice are
	stored at runtime, must be writable by the user the clam runs as. Defaults
	to current working directory if not set.
*documentation_url* (string)
	URL for extra documentation
*sourcerepo* (string)
	Link to a source code repository where the source code of the webservice or
	the underlying tool is maintained
*termsofservice* (string)
	The terms of service, either full text or a URL.
*disable_input_download* (boolean)
	Set this to _true_ if you don't want users to download input files. This can
	prevent the service being abused as a file sharing service.
*disable_ui* (boolean)
	Set to _true_ to disable the web UI entirely, only the Web API will be
	available then.
*custom_css* (string)
    Custom stylesheet to associate with the web UI. Use a full URL or start with / (i.e. relative to url)
*custom_js* (string)
    Custom javascript to associate with the web UI. Use a full URL or start with / (i.e. relative to url)

Example:


```
name = "example"
description = "Example Webservice"
authors = [ "Maarten van Gompel" ]
affiliation = "CLST, Radboud University"
termsofservice = "Use and adapt this example as you please"
rootdir = "./data"
version = "0.1"
url = "http://127.0.0.1:8080"
```

# LICENSE CONFIGURATION

You can have one *license* section (table in TOML's vocabulary) with the following fields:

*name* (string, mandatory)
	The human-readable name of the webservice
*id* (string)
	The SPDX identifier for the license
*url* (string)
	A URL where the full license can be obtained.

Example:

```
[license]
name = "GNU Affero General Public License"
id = "AGPL-3.0-only"
url = "https://www.gnu.org/licenses/agpl-3.0.en.html"
```

# CONTACT CONFIGURATION

You can have one *contact* section that gives the users of your service contact
information. It has the following fields:

*name* (string)
	Identifying name of the contact person or organization of the webservice.
*email* (string)
	Email of the contact person or the organization of the API.
*url* (string)
    Url associated with the contact

Example:

```
[contact]
name = "Maarten van Gompel"
url = "https://proycon.anaproy.nl"
email = "proycon@anaproy.nl"
```

# AUTHENTICATION CONFIGURATION

You can have one *auth* section with the following fields:

*user_file* (string)
	Path to a tab separated file that holds user names and hashed passwords for HTTP Basic
	Authentication. Setting this enables HTTP Basic Authentication.
*oauth_config_file* (string)
	Path to a TOML file that holds the configuration for OpenID Connect. Setting this
	enabled OpenID Authentication. 

Note that these two options refer to external files as this is sensitive
information which you do not want to keep with the main configuration nor inside
e version controlled repository.

## USER_FILE

The user file is a simple tab separated file with on each line a username, a tab and a SHA256 hashed password (hex notation).

## OAUTH_CONFIG_FILE

The TOML configuration file for OpenID Connect has the following mandatory fields:

*openid_configuration_url* (string)
	The URL at which the provider's configuration can be automatically retrieved from the
	OpenID Connect provider. Following the spec, this is often a URL that ends in `.well-known/openid-configuration`
	Manual configuration is not supported.
*oauth_client_id* (string)
	The ID for your service, as registered with the remote provider.
*oauth_client_secret* (string)
	The secret for your service, as registered with the remote provider.
*oauth_client_scope* (list of strings)
	The Oauth scope, this is at least always: `[ "openid" ]`

Example:

```
openid_configuration_url = "https://oidc-provider.example.org/.well-known/openid-configuration"
oauth_client_id = "myservice"
oauth_client_secret = "mysecret"
oauth_scope = [ "openid" ]
```

# ENDPOINTS CONFIGURATION

TODO: To be written...

# FILETYPES CONFIGURATION

TODO: To be written...

# VIEWERS CONFIGURATION

TODO: To be written...

# BACKGROUND_SERVICES CONFIGURATION

TODO: To be written...

# DISPATCHER CONFIGURATION

TODO: To be written...

# TEMPLATING OR ENVIRONMENT VARIABLES

In production situations, you often want to inject values into your configuration
via environment variables. For example:, the base URL is something that
you often want to make configurable as in the following example:

```
url = "$BASE_URL"
```

CLAM itself does **NOT** support this syntax directly, but relies on external tools like `envsubst` to do this for you.
The procedure is simple:

- have your service configuration in a template file like `yourservice.def.toml`, edit only this file and commit it your git repository.
- Generate the final configuration from your template file with envsubst: `envsubst < yourservice.def.toml > yourservice.toml` . We recommend to have a `Makefile` handle this for you.
- Run `clam --config yourservice.toml` as usual.


# SEE ALSO

*clam*(1)
*envsubst*(1)

# AUTHORS

Maarten van Gompel <proycon@anaproy.nl>, Centre for Language and Speech Technology, Radboud University

# ACKNOWLEDGEMENT

Developed in the scope of the Macroscope Project
Earlier versions were developed in the scope of the CLARIN-NL and CLARIAH-NL projects.
