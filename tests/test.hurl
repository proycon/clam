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

# Parameter test: integer out of bounds
GET http://127.0.0.1:8080/paramtest?int=11
accept: text/plain
HTTP 400
Content-type: application/json
[Asserts]
jsonpath "$.type" == "ParameterError"


# Project test: Project creation (PUT)
PUT http://127.0.0.1:8080/testproject
HTTP 201

# Project test: Project status (GET)
GET http://127.0.0.1:8080/testproject
HTTP 200
Content-type: application/json
[Asserts]
jsonpath "$.stage" == "Staging"

# Project test: File upload (PUT)
PUT http://127.0.0.1:8080/testproject/inputtxt/hello.txt
Content-type: text/plain
```
hello world!
```
HTTP 201

# Project test: Input file download
GET http://127.0.0.1:8080/testproject/inputtxt/hello.txt
HTTP 200
[Asserts]
```
hello world!
```

# Project test: Project execution (POST)
POST http://127.0.0.1:8080/testproject
HTTP 200

# Project test: Project status 1/2 (GET)
GET http://127.0.0.1:8080/testproject
[Options]
delay: 1s
HTTP 200
Content-type: application/json
[Asserts]
jsonpath "$.stage" == "Running"

# Project test: Project status 2/2 (GET)
GET http://127.0.0.1:8080/testproject
[Options]
delay: 5s
HTTP 200
Content-type: application/json
[Asserts]
jsonpath "$.stage" == "Done"

# Project test: Project deletion (DELETE)
DELETE http://127.0.0.1:8080/testproject
HTTP 204

# Project test: Verify deletion (GET)
GET http://127.0.0.1:8080/testproject
Content-type: application/json
HTTP 404
