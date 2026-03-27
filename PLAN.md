# CLAM v4.0 -- Plan

*2026-03-27 -- Maarten van Gompel, Humanities Lab, Radboud University Nijmegen*

## Introduction

CLAM is a tool to turn command-line tools into RESTFUL webservices with a
generic web user-interface. It is particularly suited for batch processing of
multiple input files that undergo some kind of transformation and are
subsequently turned into one or more output files. It was designed 16 years
ago, which means that some design decisions no longer live up to current
best-practises and the code-base has a lot of tech-debt. We use CLAM for over a
dozen webservices at Radboud University.

The user interface currently renders client-side in the user's browser via
XSLT, based on the XML-responses CLAM provides. XSLT is being deprecated by all
major browser so this will cease to function around november 2026 (see
https://github.com/proycon/clam/issues/114). This will be patched in CLAM v3.3
but the solution it not ideal so this led to the idea for a more rigorous and
ambitious solution:

In order to sustainably offer webservices for the future, the idea arose to
redesign and reimplement CLAM. This would be a complete rewrite that is **NOT**
backwards compatible, but instead offers a sustainable future-oriented
solution. I call this CLAM v4 because it solved the same problem and am
attached to the name by now, the codebase would be wholly new.

## Features

The following features are planned:

* The new CLAM v4 implementation will be more minimal compared to the current CLAM
* Use simpler and more contemporary JSON-based responses for the Web API (instead of XML)
* Support both OAuth2/OpenID Connect and HTTP Basic Authentication  (like current CLAM)
* Loosen the strict determinism requirement that the current CLAM imposes, this will add
  some more flexibility to how CLAM can be used.
* No metadata keeping, this functionality of CLAM wasn't used much by end-users.
* Implementation in Rust (instead of Python), using the axum web framework
* Improved performance (also greatly facilitated by the above)
* Webservices themselves are fully language-agnostic (no Python bias, nor Rust)
* Adhere to OpenAPI standards, produce an OpenAPI/swagger specification on-the-fly
* Support for both batch as well as non-batch (quick roundtrip) execution (the latter corresponds to the 'action' mode in the current CLAM)
* Implement a pending job queue so users will no longer be presented with a HTTP 503 if the system is too busy
* There will extra attention to security.
* Extra attention for use-cases in which resource-sharing such as GPU-sharing is a factor.

## Planning

The project is fairly tight and ambitious. Ideally, a first fully functional release
would be due in October 2026, so we can migrate webservices in time for the
final XSLT removal from browsers. If this is not feasible yet, CLAM v3.3 acts
as a temporary fallback solution and the project would run to the end of the year.

Planning is somewhat complicated by the fact that I have only 0.2 fte for this
task and I'll have to find some consecutive time to make real progress and
juggle with priorities elsewhere. A very conservative and rough total hour estimate is 250
hours, but this likely an underestimate that will be exceeded. The following
phases can be distinguished, but I can't really pin any dates on them:

1. Planning and brainstorming
2. Initial skeleton
3. Configuration parsing
4. Process queuing and dispatching
5. Authentication
6. Web User interface

Conversion/migration of existing webservices is a separate project after this.

## Ethics

* The software will be licensed under AGPLv3
* No AI/LLM will be used in this project
