# TODO

## Backlog

- [ ] UI polishing
    - [ ] Pagination for input and output files
    - [ ] Test interface on mobile devices
    - [ ] Less intrusive status page refreshes
- [ ] Fix swagger validator errors (see bottom-right corner of swagger UI)

## In progress


## Done but need testing

- [x] Implement a mechanism for project transfer between users
    -  This also accommodates projects like the CLARIN switchboard.
       It can create a project and upload files with its own API key;
    - [x] It then calls a *transfer* endpoint to release the project *to* (query parameter) a particular user (or `*` for anybody).
    - [x] The user the *transfer* endpoint to claim the project *from* (query parameter) a particular user.
          This URL can be provided to the user by a tool like the Switchboard after it has released a project.
          The challenge is that the users will land on an unauthenticated endpoint and the project name and sender have to be carried over until after the user authenticated.
- [ ] Basic auth in hybrid/production setting

## Done

- [x] Fix OpenAPI/swagger endpoint
- [x] oidc: query userinfo endpoint for user email
- [x] Expire sessions
- [x] Fix output files and viewer path, missing prefix
- [x] Add logout function for OIDC (clear cookies)
- [x] UI: add some UI error messages instead of raw json
- [x] Propagate error feedback when a background job fails
- [x] Implement viewers
    - Viewers will be kept as simple as possible and use the existing command/job structure. If external services are desired then users need to implement a script for it.
- [x] Fix job monitoring thread (stderr,stdout are not drained concurrently)
- [x] Write documentation for service configuration files
- [x] Search for commands in $PATH so they don't have to be absolute (without invoking a shell)
- [x] Generate random project name if none was specified in UI
- [x] Test HTTP Basic Authentication
- [x] Test OpenID Connect Authentication
