# TODO

## Backlog

- [ ] Implement a mechanism for project transfer between users
    -  This also accommodates projects like the CLARIN switchboard.
       It can create a project and upload files with its own API key;
    - [ ] It then calls a *transfer* endpoint to release the project *to* (query parameter) a particular user (or `*` for anybody).
    - [ ] The user the *transfer* endpoint to claim the project *from* (query parameter) a particular user.
          This URL can be provided to the user by a tool like the Switchboard after it has released a project.
          The challenge is that the users will land on an unauthenticated endpoint and the project name and sender have to be carried over until after the user authenticated.
- [ ] Test interface on mobile devices
- [ ] Generate random project name if none was specified in UI

## In progress


## Done

- [x] Test OpenID Connect Authentication
- [x] Test HTTP Basic Authentication
- [x] Implement viewers
    - Viewers will be kept as simple as possible and use the existing command/job structure. If external services are desired then users need to implement a script for it.
- [x] Fix job monitoring thread (stderr,stdout are not drained concurrently)
- [x] Search for commands in $PATH so they don't have to be absolute (without invoking a shell)
- [x] Write documentation for service configuration files
