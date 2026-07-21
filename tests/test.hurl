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
