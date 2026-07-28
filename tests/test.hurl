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

# Action test: empty parameter test
GET http://127.0.0.1:8080/paramtest
accept: text/plain
HTTP 200
Content-type: text/plain
[Asserts]
```
-f 3.14
```

# Parameter test: boolean
GET http://127.0.0.1:8080/paramtest?bool=1
accept: text/plain
HTTP 200
Content-type: text/plain
[Asserts]
```
-b -f 3.14
```

# Parameter test: string
GET http://127.0.0.1:8080/paramtest?string=hello%20world
accept: text/plain
HTTP 200
Content-type: text/plain
[Asserts]
```
-f 3.14 -s hello world
```

# Parameter test: int
GET http://127.0.0.1:8080/paramtest?int=5
accept: text/plain
HTTP 200
Content-type: text/plain
[Asserts]
```
-i 5 -f 3.14
```
