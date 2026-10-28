clam(5)

# NAME

clam - Turns command-line applications into RESTful webservice with a web-interface, so both automated client and humans can interact with your tool over the web.

# INTRODUCTION

A CLAM service is configured via a single configuration file in *TOML* syntax.
See https://toml.io/en/ for generic information about TOML if you are not
familiar with the syntax. It greatly helps the reading of this document to be
acquainted with it.

# TABLE OF CONTENTS

- _GENERAL CONFIGURATION_
- _LICENSE CONFIGURATION_
- _CONTACT CONFIGURATION_
- _AUTHENTICATION CONFIGURATION_
- _ENDPOINTS CONFIGURATION_
	- _ENDPOINT COMMAND CONFIGURATION_
	- _ENDPOINT PARAMETER CONFIGURATION_
	- _PARAMETER TYPES_
	- _OUTPUT TYPES CONFIGURATION_
- _FILETYPES CONFIGURATION_
- _VIEWERS CONFIGURATION_
- _BACKGROUND SERVICES CONFIGURATION_
- _DISPATCHER CONFIGURATION_
- _TEMPLATING OR ENVIRONMENT VARIABLES_

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
a version controlled repository.

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

When you register your webservice with your openid provider, make sure to always provide the
following redirect URL (substitute the example domain for your own):

```
https://yourservice.example.org/oidc/callback
```

# ENDPOINTS CONFIGURATION

The endpoints form the heart of the service configuration, here you determine what
happens when users access a certain URL/path on your service. There are several
types or *modes* of endpoints:

- *LandingPage* - This is a generic public landing page for your webservice, you
  almost always want to serve this at `/`. From here, all the other parts are
  accessible via the Web UI.
- *Project* - In project mode, responses do not come immediately after a _POST_
  request but clients poll for status at regular intervals using a _GET_ request
  and must first create (_PUT_/_POST_) a project and optionally (_PUT_/_POST_)
  files. Users can _DELETE_ projects when done, or leave them to come back later.
  This allows the job to run over long periods of time and allows (multiple)
  file-based input and output (batch processing). All project endpoint paths are suffixed
  with the project ID. The _GET_ endpoint presents the staging area (files), an in progress state, or the
  output files, depending on the state of the project
- *Action* - In action mode, a single response follows immediately upon a POST
  request. This assumes the job runs in limited time with singular output only. No
  file upload/download support. A _GET_ on this endpoint (requesting HTML) presents
  the interface for that action.

We will first show an example of each mode, and then discuss the fields:

```
[[endpoints]]
name = "Landing page"
path = "/"
mode = "LandingPage"
public = true
```

*path* (string)
	The path where the endpoint is accessible, this also serves as the primary identifier for the endpoint. All paths must begin with a slash (/) and should NOT have an additional trailing slash
*name* (string)
	Human-readable name or title of the endpoint
*summary* (string)
	Short summary of the endpoint (for human end-users)
*description* (string)
	Larger description of the endpoint, supports CommonMark syntax. (for human end-users)
*mode*
	The mode of the endpoint, can be *LandingPage*, *Project* or *Action*, see
	the explanation at the beginning of this section.
*public* (bool)
	Set to true to make this endpoint public (requiring authentication), otherwise it defaults to private if authentication is enabled, and public if no authentication was set up at all.
	It is discouraged to make any *Project* endpoints public.
*parameters*
	Defines input parameters that can be set by the user. See the section _ENDPOINT PARAMETER CONFIGURATION_ further below. 
*background_services* (list of strings, ids of background services)
	List of background services to start for this endpoint, they are referred to by their ID. This refers
	to services you defined in the root-level *background_services* section. Read section _BACKGROUND SERVICES CONFIGURATION_.
	CLAM will ensure that the background service is up whenever this endpoint is used.

## ENDPOINT COMMAND CONFIGURATION

*command* (string)
	Command to invoke, just the executable without any arguments (those are in _args_).
	This can be any tool or script in any language. In non-trivial situations it
	is common to write a so-called *wrapper script* and put that here,
	and have the wrapper script call the actual underlying tool and perform
	some of the necessary translations you need. Whatever tool or script you
	call, _it is vital that it respects exit code conventions_ and returns exit
	code 0 on success and non-zero on failure. Furhtermore, in action mode (and for viewers),
	CLAM interprets interprets exitcodes 40,43 and 44, and maps them to,
	respectively HTTP 400 (Bad Request), HTTP 403 (Permission Denied), and HTTP
	404 (Not Found). Any other error will result in a HTTP 500 (Internal Error).
*args*
	Arguments to pass to the command. These can be either literal arguments,
	(e.g. _args = [ "-a","-b","--foo","bar" ]_ or
	explicit references to parameters from which the value should be taken. If
	you just leave this empty, all parameters you defined will be automatically converted
	to command arguments. This is simplest and often what you want. If you do populate this 
	yourself _and_ still want this automatic
	behaviour too, set _auto_add_args = true_. This is used mainly in situations
	where you have some literal arguments first, and want the rest to be derived
	from the parameters. Referencing parameters explicitly
	takes the following form (repeat for every parameter you want in the command
	arguments):

```
[[endpoints.args]]
parameter_id = "someparameter"
```

*auto_add_args* (boolean)
	Automatically add all parameters to the arguments (If you didn't specify 'args' at all, then this is enabled by default),
*status_pattern* (regular expression, rust notation)
	This is a regular expression that matches with the stderr output of your
	tool and records all matches for logging in the status log.
*filetype* (string, id of a filetype)
	The file type of the output, used with only with endpoints in *Action* mode.
	This refers back to file type you defined in the root level *filetypes*
	section. Read section _FILETYPES CONFIGURATION_ further below.
*output_files*
	Defines what output files can be expected. Only used with endpoints in
	*Project* mode.
	See section _OUTPUT FILES CONFIGURATION_ further below.


## ENDPOINT PARAMETER CONFIGURATION

Parameters are exposed by the service to be set by the end-user. They will be
be converted into command line arguments as seen in the section
_ENDPOINT_COMMAND_CONFIGURATION_ above.

The order in which the parameters are defined is also the order they appear in
the interface.

A parameter entries have a type, we will enumarate all of them in the following
example and then discuss the individual fields:

```
[[endpoints.parameters]]
id = "bool"
name = "Boolean test"
description = "Boolean test parameter"
required = false
type = { parametertype = "Bool", default = false }
flag = "-b"

[[endpoints.parameters]]
id = "int"
name = "Integer test"
description = "Integer between 1 and 10"
required = false
type = { parametertype = "Int", min = 1, max= 10  }
flag = "-i"

[[endpoints.parameters]]
id = "float"
name = "Float test"
description = "Float test parameter with default"
required = false
type = { parametertype = "Float", default = 3.14  }
flag = "-f"

[[endpoints.parameters]]
id = "string"
name = "String test"
description = "String test parameter"
required = false
type = { parametertype = "String"  }
multiple = true
flag = "-s"

[[endpoints.parameters]]
id = "selection"
name = "Selection test"
description = "Selection test parameter"
required = false
flag = "-S"

[endpoints.parameters.type]
parametertype = "Selection"
choices = [ "apple", "pear", "banana" ]
default = [ "pear" ]
```

The fields are:

*id*
	Identifier for the parameter, used as variable name in url-encoded queries or fields in multipart data (depending on context)
*name*
	Human-readable name for the parameter, this is what will be shown in the interface.
*type*
	The type of parameter, this also carries extra constraints you want to impose. See the examples above and the section _PARAMETER TYPES_ below.
*required* (boolean)
	Determines if the parameter is mandatory to be provided by the user
	(defaults to false)
*flag* (string)
	the full parameter flag that is used to pass this parameter to the underlying tool, this includes any = sign
	Leave empty for positional arguments
*multiple* (boolean)
	Allow multiple of these?
	(defaults to false)

## PARAMETER TYPES

Parameter types have the following fields:

*parametertype* (mandatory)
	One of: String, Int, Float, Bool, Selection or file
*min* (int or float, optional)
	The minimum value for this parameter (for Int or Float only)
*max* (int or float, optional)
	The maximum value for this parameter (for Int or Float only)
*maxlength* (int, optional)
	The maximum length in characters for this parameter (for String only)
*validation_pattern* (string, optional)
	Validation pattern in Rust notation, this will be used server-side. Please also specify `validation_pattern_js` for client-side validation if you use the interface.
*validation_pattern_js* (string, optional)
	Client-side validation pattern in javascript notation, please specify this if you specify `validation_pattern`
*default* (int,float,string, list, optional)
	Default value for the parameter, if the user didn't supply it.
*filename* (table, mandatory only for File)
	The filename field determines what the name of the file should adhere to, it
	can either be an exact filename or a regular expression pattern (allowing
	some liberty to the user). If the parameter has `multiple = true`, you
	should always use a pattern. Examples of both:

```
filename = { nametype = "Exact", value = "test.txt" }
```

```
filename = { nametype = "Pattern", value = "\\.txt$" }
```

*filetype* (string, mandatory only for File)
	This refers to an ID you defined in *filetypes*, see Section _FILETYPE
	CONFIGURATION_ further below.
*choices* (list of strings)
	All possibler values for this (only for Selection)
*multiple* (boolean)
	Allow multiple choices (only for Selection), defaults to false

## OUTPUT FILES CONFIGURATION

This is only used for endpoints in *Project* mode and defines the types of files
that can be expected.

An entry for each output file looks as follows:

```
[[endpoints.outputfiles]]
name = "Output text"
type = "plaintext"
filename = { nametype = "Pattern", value = "\\.txt$" }
```

*name* (string, mandatory)
	Human-readable name for the output file
*type* (string, mandatory)
	This refers to an ID you defined in *filetypes*, see Section _FILETYPE
	CONFIGURATION_ below.
*filename* (table, mandatory)
	The filename field is used to match against output files.
	You can match either on exact filename or on a regular expression pattern.
	The syntax is the same as explained in the previous section.

# FILETYPES CONFIGURATION

At the global level, you define which file types your service may take as input
or produce as output. Note that CLAM itself does not predefine any. A filetype
entry looks as follows, repeat it for each filetype:

```
[[filetypes]]
id = "plaintext"
name = "Plain Text (UTF-8)"
contenttype = "text/plain; charset=utf-8"
viewers = [ "textviewer" ]
```

It has the following fields:

*id* (string, mandatory)
	The identifier of the filetype, this is used to refer back to it from
	*endpoints.outputfiles*, *endpoints.filetype*, *endpoints.parameters.parametertype* (=File) and various other places.
*name* (string, mandatory)
	Human-readable label for this file type.
*contenttype* (string, mimetype, mandatory)
	This is the MIME type that will be used for _Content-Type_ in HTTP responses for this filetype.
*viewers* (list of strings of viewer identifiers, optional)
	This is a list of viewers (referenced by ID) to visualise this file type
	from the web interface. See section _VIEWERS CONFIGURATION_ below.

# VIEWERS CONFIGURATION

In CLAM, a viewer is effectively an external tool that converts a file to output
suitable for visualisation (HTML by default). CLAM does not predefine any
viewers, these are external scripts of your own that are invoked similar to
*Action* endpoint; they run once, fairly quickly, and return output.

A particularity of viewers, however, is that they may take input via standard
input (i.e. the contents of the file they are to visualise).

Viewers are tied to file types and shown in the web interface, giving users
the option to visualise output files.

If your viewer relies on an external webservice, it is your task to implement that
logic in the script you invoke for your viewer.

First consider the following example of a simple viewer for plain text files,
that effectively only escapes certain characters for HTML output:

```
[[viewers]]
id = "textviewer"
name = "Text Viewer"
embed = true
command = "sed"
args = [ "-e", "s/&/\\&amp;/g", "-e" , "s/</\\&lt;/g", "-e", "s/>/\\&gt;/g", "-e", "s/\\n/<br>/g" ]
```

This uses sed for some simple replacements (do mind the extra espacing because of
TOML syntax), it is fed via standard input and outputs to standard output.

In *args*, we allow for one special parameter named _FILE_ to be used as a
substitute for the input file, in that case it is no longer passed over standard
input and the same funcionality could be implemented as:

```
[[viewers]]
id = "textviewer"
name = "Text Viewer"
embed = true
command = "sed"
args = [ "-e", "s/&/\\&amp;/g", "-e" , "s/</\\&lt;/g", "-e", "s/>/\\&gt;/g", "-e", "s/\\n/<br>/g", "FILE" ]
```

Viewers take the following fields:

*id* (string, mandatory)
	The identifier of the viewer, this is used to refer back to it from
	*endpoints.outputfiles* and will also appear in URLs.
*name* (string, mandatory)
	Human-readable label for this viewer type.
*embed* (boolean)
	Embed the viewer output in the default CLAM UI, this assumes the output only sends partial HTML (no html/head/body tags)
	Headers and footers will be added automatically. If this is not set (which
	is the default), then the viewer controls the entire output.
*contenttype* (string, mimetype, optional)
	This is the MIME type that will be used for _Content-Type_ in HTTP responses for this viewer.
	If not set, if defaults to `text/html; charset=utf-8`.
*command* (string, mandatory)
	Command to invoke, just the executable without any arguments (those are in `args`)
*args* (list of strings)
	Arguments to pass to the command. These are either literal arguments or the special
	value _FILE_, which will be substituted with the path to the input file on the
	file system.

# BACKGROUND SERVICES CONFIGURATION

Certain systems have a large initialisation time as they for instance
load a model into RAM/vRAM. Furthermore, this is often shared memory that does
not necessarily need to be reinitialised for every user and every requests.

In such scenarios, the underlying tools CLAM invokes via *Action* endpoints and *Project*
can be implemented in such a way, that they rely on an an additional
service that holds the shared model, rather than loading it themselves.
Communication with the shared service proceeds then often proceeds over the
network (even if that may be completely local).

For tools that implement such a client/server model, CLAM has a feature called
*background services* that facilitates starting and stopping the shared server part.

It works as follows, whenever a request comes in on an *Action* or *Project*
instance that has background services defined, CLAM ensures first that the
background services are started. Only then is the tool called. The background
services are shared by all requests, so only one of each is started, regardless
of the number of requests and number of users (note: CLAM does not implement
any scaling solutions). When a request is completed and job has run, CLAM either
keeps background service active indefinitely or until a certain idle time has
passed, at which point it can be automatically unloaded again. This unloading
allows freeing precious system resources when they are not used.

This implies that the first user/request pay a time penalty because the
background service has to be initialised, but subsequent requests will be very
fast. You can of course also have CLAM start all background services at startup
if system resource are no concern.

An example of a background service:

```
[[background_services]]
id = "modelserver"
description = "Loads a model"
command = "modelserver.sh"
args = [ "--port", "1111" ]
unload_time = 600
```

The following fields are available:

*id* (string, mandatory)
	The identifier of the background service, this is used to refer back to it from
	*endpoints.background_services* and *viewers.background_services*
*description* (string, optional)
	Human-readable description of the backgrounds service
*command* (string, mandatory))
	Command to invoke, just the executable without any arguments (those are in `args`).
	This can be any tool or script in any language. In non-trivial situations it
	is common to write a so-called *wrapper script* and put that here,
	and have the wrapper script call the actual underlying tool and perform
	some of the necessary translations you need. Whatever tool or script you
	call, *it is vital that it respects exit code conventions* and returns exit
	code 0 on success and non-zero on failure. Furthermore, in action mode (and for viewers),
	CLAM interprets interprets exitcodes 40,43 and 44, and maps them to,
	respectively HTTP 400 (Bad Request), HTTP 403 (Permission Denied), and HTTP
	404 (Not Found). Any other error will result in a HTTP 500 (Internal Error).
*args* (list, optional)
	Literal arguments to pass to the command. Note that these can never be
	parametrised by the end-user like with endpoints.
*unload_time* (int)
	Unload time in seconds: after this many seconds of idle time the background service will be stopped again.
	If not set (default), background services are kept running indefinitely.
*autostart* (bool)
	Autostart the background service on CLAM startup, rather than on first request.
	Useful if you run the background service indefinitely.
*status_pattern* (regular expression, rust notation)
	This is a regular expression that matches against the stderr output of your
	tool and records all matches, it can be forwarded to the user in case the
	background service fails.
*up_pattern* (regular expression, rust notation)
	This is a regular expression that matches against the stderr output of your
	tool. It is meant to catch the phrase in your log that indicates
	that your service is ready to accept connections. CLAM waits for this signal before
	starting jobs that depend on this background service.
	If this is not set, services are assumed to be ready right away after start.


# DISPATCHER CONFIGURATION

The dispatcher is the part of CLAM that executes and monitors the jobs (
processes) it runs. Its behaviour can be controlled, the following example
shows the default configuration that is used when you omit the entire section:

```
[dispatcher]
max_running_jobs = 100
max_total_jobs = 1000
checkbackgroundservices_interval = 60
```

The fields are:

*max_running_jobs* (int)
	Maximum number of running jobs at the same time. Note that this also includes background service jobs.
*max_total_jobs* (int)
	Maximum number of jobs waiting in the queue, if full, HTTP 503 will be returned. note that this also includes background service jobs.
*checkbackgroundservices_interval* (int)
	Interval in seconds to check background services and spin them down if necessary.

# TEMPLATING OR ENVIRONMENT VARIABLES

In production situations, you often want to inject values into your configuration
via environment variables. For example:, the base URL is something that
you often want to make configurable as in the following example:

```
url = "$BASE_URL"
```

CLAM itself does **NOT** support this syntax directly, but relies on external tools like _envsubst_ to do this for you.
The procedure is simple:

- have your service configuration in a template file like _yourservice.def.toml_, edit only this file and commit it your git repository.
- Generate the final configuration from your template file with _envsubst_. We recommend to have a _Makefile_ handle this for you.

```
envsubst < yourservice.def.toml > yourservice.toml` . 
```

- Then start as usual:

```
clam --config yourservice.toml
```


# SEE ALSO

*clam*(1)
*envsubst*(1)

# AUTHORS

Maarten van Gompel <proycon@anaproy.nl>, Centre for Language and Speech Technology, Radboud University

# ACKNOWLEDGEMENT

Developed in the scope of the Macroscope Project.
Earlier versions were developed in the scope of the CLARIN-NL and CLARIAH-NL projects.
