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
	Base path on the file system where the user files for the webservice are stored at runtime, must be writable by the user the clam runs as. Defaults to current working directory if not set.
*documentation_url* (string)
	URL for extra documentation
*sourcerepo* (string)
	Link to a source code repository where the source code of the webservice or the underlying tool is maintained

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

TODO: To be written...

# FILETYPES CONFIGURATION

TODO: To be written...

# ENDPOINTS CONFIGURATION

TODO: To be written...

# BACKGROUND_SERVICES CONFIGURATION

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
