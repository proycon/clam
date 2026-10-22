# CLAM

CLAM turns command-line applications into RESTful webservice with a
web-interface, so both automated client and humans can interact with your tool
over the web.

## Introduction

CLAM expects a description of your tool in the form of desired endpoints,
commands to call, input parameters to pass on, and expected input & output
formats. All this is provided in a configuration file.

CLAM is set up in a
generic fashion and requires minimal effort on the part of the service
developer. Your actual application is treated as a black box, of which only the
parameters, input formats and output formats need to be described. Your
application itself needs not be network aware in any way, nor aware of CLAM,
and the handling and validation of input can be partially taken care of by
CLAM.

Users call your tool over the web, via CLAM, by filling the necessary
parameters and (if needed) uploading input files. They then start the system
and are presented the output, which may consist of multiple files.

CLAM is suitable both for simple runs with a quick turn-around (we call them
**actions**), as well as batch processing which may take a long time to process
in the background (we call those **projects**). Actions provide a response
immediately, projects need to be *polled* at a regular interval for their
completion status. Unlike actions, projects allow multiple input and output
files. Users can come back to their projects to inspect the output at any time
until they explicitly deleted the project.

## Features

* **Human & Machine interface**: Designed both for automated clients as-well as human end-users.
    * **OpenAPI REST API**: The webservices you create with CLAM are fully described by an [OpenAPI](https://openapis.org) specification that is automatically generated on the basis of the configuration you provide. An additional Swagger interface is available for humans to serve as API documentation.
    * **Simple generic webinterface**: CLAM offers a simple generic web UI for human end-users. It is a server-side multi-page-application with only minimal vanilla Javascript and no additional client-side frameworks/libraries.
* Supports both long-running **batch jobs** with multiple input and output files (**projects**), as well as quick request-response jobs (**actions**)
* **Authentication**: Choose between two forms of authentication (or none at all, not recommended if you make use of **projects**)
    * HTTP Basic Authentication
    * OpenID Connect (OIDC) Authentication
    * The two can be used simultaneously if needed.
* **Background services**: Support for long-running background services that are shared between runs from multiple users. CLAM takes care of starting when they're used and stopping them when they have been idle for a while. This is useful if your underlying application has a client/server model and/or relies on
large in-memory models (also on GPU).
* **Viewers**: You can tie in viewers to visualise output files of certain types. Viewers are simply your own scripts or tools that convert a certain format to HTML.
* **Automatic Job Scheduling**: Projects that can't be run right away due to lack of system resources are scheduled and picked up when resources are available again.

CLAM v4 is written in Rust, but it is completely agnostic to your underlying
tool which can be written in any language. It aspires to be a fairly
**minimal** yet flexible tool you can use to wrap around your own tools and
scripts to be able to serve them over the web. CLAM is **written with full
human attention without AI/LLMS**, no parts have been vibe-coded or written by
agents. The [contributor guidelines](CONTRIBUTING.md) ensure it stays this way.

## Installation

For the time being (pending release and packaging), install CLAM by cloning this git repository and running:

```
$ make
$ sudo make install
```

You just need `cargo` (the rust packager) and `rustc` (the Rust compiler) for this. On a Debian/Ubuntu Linux system, they can be installed with:
`apt install cargo rustc`.

If you want it in a custom location and possibly without superuser permissions, you can do something like this instead:

```
$ PREFIX=~/.local make install
```

## Usage

After installation, CLAM is available as `clam`.

Documentation is available in manual pages (and online):

* See `man clam` (or [here](/docs/clam.1.scd)) for documentation on running CLAM.
* See `man 5 clam` (or [here](/docs/clam.5.scd)) for documentation on writing a service configuration file for your CLAM webservice.

## History

CLAM was created in 2010 and has been in use and development ever since. The
current incarnation, version 4, however, is a complete rewrite that is no
longer backward compatible with versions 3 and below, which were written in
Python and user their own API and XML formats. Both the implementation as well
as the configuration syntax have changed completely. So if you want to upgrade
your webservice from CLAM 3 to CLAM 4, you will need to rewrite it. After 16
years, some of the fundamental principles in the old implementation needed to
be revised and modernised for CLAM to make it into the future.
