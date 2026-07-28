# Get OpenAPI specification
GET http://127.0.0.1:8080/openapi.json
HTTP 200
[Asserts]
jsonpath "$.openapi" exists
jsonpath "$.info.title" == "test"
jsonpath "$.servers[0].url" == "/"
jsonpath "$.paths" exists


# Root URL also gives OpenAPI specification when json is requested
GET http://127.0.0.1:8080/
accept: application/json
HTTP 200
[Asserts]
jsonpath "$.openapi" exists


# Project index
GET http://127.0.0.1:8080/projects
accept: application/json
HTTP 200
[Asserts]
jsonpath "$" count == 0


# Non-existent project
GET http://127.0.0.1:8080/non-existent-project
accept: application/json
HTTP 404

# Action test
GET http://127.0.0.1:8080/uppercase?text=hello%20world
accept: text/plain
HTTP 200
Content-type: text/plain
[Asserts]
```
HELLO WORLD
```
