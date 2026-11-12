Create comprehensive test cases for the API. 
Provide: 
1. curl commands to test each endpoint 
2. Example JSON payloads for POST and PUT requests 
3. Expected responses for successful operations 
4. Test cases for error scenarios (missing fields, invalid data, course not found) 

# Response

Start the application:

```bash
python app.py
```

Set the API URL:

```bash
export BASE_URL="http://127.0.0.1:5000"
export COURSE_ID=1
```

# 2. Successful Operation Tests

## 2.1 Get All Courses

```bash
curl -i -X GET "$BASE_URL/courses" \
  -H "Accept: application/json"
```

Expected response:

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

Example response body:

```json
[
  {
    "id": 1,
    "name": "Introduction to Software Engineering",
    "description": "Fundamentals of software engineering.",
    "instructor": "Dr. Smith"
  },
  {
    "id": 2,
    "name": "Artificial Intelligence",
    "description": "Introduction to AI concepts and applications.",
    "instructor": "Dr. Jones"
  }
]
```

If there are no courses, the expected response may be:

```json
[]
```

## 2.2 Get a Course by ID

```bash
curl -i -X GET "$BASE_URL/courses/$COURSE_ID" \
  -H "Accept: application/json"
```

Expected response:

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

Example response body:

```json
{
  "id": 1,
  "name": "Introduction to Software Engineering",
  "description": "Fundamentals of software engineering.",
  "instructor": "Dr. Smith"
}
```

## 2.3 Create a Course

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "Database Systems",
    "description": "Relational databases, SQL, and database design.",
    "instructor": "Dr. Williams"
  }'
```

Expected response:

```http
HTTP/1.1 201 Created
Content-Type: application/json
```

Example response body:

```json
{
  "id": 3,
  "name": "Database Systems",
  "description": "Relational databases, SQL, and database design.",
  "instructor": "Dr. Williams"
}
```

Some implementations may return `200 OK` instead of `201 Created`.

## 2.4 Update a Course

```bash
curl -i -X PUT "$BASE_URL/courses/$COURSE_ID" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "Advanced Software Engineering",
    "description": "Advanced software architecture, testing, and maintenance.",
    "instructor": "Dr. Smith"
  }'
```

Expected response:

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

Example response body:

```json
{
  "id": 1,
  "name": "Advanced Software Engineering",
  "description": "Advanced software architecture, testing, and maintenance.",
  "instructor": "Dr. Smith"
}
```

Verify that the update was saved:

```bash
curl -i -X GET "$BASE_URL/courses/$COURSE_ID" \
  -H "Accept: application/json"
```

## 2.5 Delete a Course

```bash
curl -i -X DELETE "$BASE_URL/courses/$COURSE_ID" \
  -H "Accept: application/json"
```

Expected response:

```http
HTTP/1.1 200 OK
```

Example response body:

```json
{
  "message": "Course deleted successfully"
}
```

A REST API may instead return:

```http
HTTP/1.1 204 No Content
```

Verify that the course was deleted:

```bash
curl -i -X GET "$BASE_URL/courses/$COURSE_ID" \
  -H "Accept: application/json"
```

Expected response:

```http
HTTP/1.1 404 Not Found
```

# 3. POST and PUT Payload Examples

## 3.1 Valid POST Payload

```json
{
  "name": "Operating Systems",
  "description": "Processes, memory management, file systems, and concurrency.",
  "instructor": "Dr. Brown"
}
```

## 3.2 Valid PUT Payload

```json
{
  "name": "Advanced Operating Systems",
  "description": "Advanced operating-system architecture and distributed systems.",
  "instructor": "Dr. Brown"
}
```

## 3.3 Payload with Unexpected Fields

```json
{
  "name": "Software Testing",
  "description": "Testing techniques.",
  "instructor": "Dr. Green",
  "unexpected_field": "unexpected value"
}
```

The API should either reject unexpected fields with `400 Bad Request` or explicitly ignore them.

# 4. Error-Scenario Tests

## 4.1 POST with No Request Body

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: application/json"
```

Expected response:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json
```

Example response:

```json
{
  "error": "Request body is required"
}
```

## 4.2 POST with Missing Name

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A course without a name.",
    "instructor": "Dr. Smith"
  }'
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

Example response:

```json
{
  "error": "Missing required field: name"
}
```

## 4.3 POST with Missing Description

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Incomplete Course",
    "instructor": "Dr. Smith"
  }'
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

## 4.4 POST with Missing Instructor

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Incomplete Course",
    "description": "This course has no instructor."
  }'
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

## 4.5 POST with Empty Values

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "",
    "description": "",
    "instructor": ""
  }'
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

## 4.6 POST with Invalid JSON

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: application/json" \
  -d '{"name": "Invalid JSON"'
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

Example response:

```json
{
  "error": "Invalid JSON"
}
```

## 4.7 POST with Invalid Data Types

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "name": 12345,
    "description": true,
    "instructor": ["Dr. Smith"]
  }'
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

## 4.8 GET for a Nonexistent Course

```bash
curl -i -X GET "$BASE_URL/courses/999999" \
  -H "Accept: application/json"
```

Expected response:

```http
HTTP/1.1 404 Not Found
```

## 4.9 PUT for a Nonexistent Course

```bash
curl -i -X PUT "$BASE_URL/courses/999999" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Course",
    "description": "This course does not exist.",
    "instructor": "Dr. Smith"
  }'
```

Expected response:

```http
HTTP/1.1 404 Not Found
```

Example response:

```json
{
  "error": "Course not found"
}
```

## 4.10 DELETE a Nonexistent Course

```bash
curl -i -X DELETE "$BASE_URL/courses/999999" \
  -H "Accept: application/json"
```

Expected response:

```http
HTTP/1.1 404 Not Found
```

## 4.11 PUT with Missing Fields

```bash
curl -i -X PUT "$BASE_URL/courses/$COURSE_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name"
  }'
```

Expected response if `PUT` requires all fields:

```http
HTTP/1.1 400 Bad Request
```

## 4.12 PUT with an Invalid Course ID

```bash
curl -i -X PUT "$BASE_URL/courses/not-a-number" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Course",
    "description": "Invalid ID test.",
    "instructor": "Dr. Smith"
  }'
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

or:

```http
HTTP/1.1 404 Not Found
```

The API should not return an unhandled `500 Internal Server Error`.

## 4.13 GET with an Invalid Course ID

```bash
curl -i -X GET "$BASE_URL/courses/not-a-number" \
  -H "Accept: application/json"
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

## 4.14 DELETE with an Invalid Course ID

```bash
curl -i -X DELETE "$BASE_URL/courses/not-a-number" \
  -H "Accept: application/json"
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

## 4.15 Unsupported HTTP Method

```bash
curl -i -X PATCH "$BASE_URL/courses/$COURSE_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Unsupported update"
  }'
```

Expected response:

```http
HTTP/1.1 405 Method Not Allowed
```

## 4.16 Wrong Content Type

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: text/plain" \
  -d 'name=Invalid&description=Invalid&instructor=Invalid'
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```

or:

```http
HTTP/1.1 415 Unsupported Media Type
```

## 4.17 Empty JSON Object

```bash
curl -i -X POST "$BASE_URL/courses" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Expected response:

```http
HTTP/1.1 400 Bad Request
```


| Syntax      | Description |
| ----------- | ----------- |
| Header      | Title       |
| Paragraph   | Text        |

## 5. Test Matrix

### Successful Tests

## 5. Test Matrix

| Test No. | Endpoint | Scenario | Expected Status |
|---:|---|---|---|
| 1 | `GET /courses` | Retrieve all courses | `200 OK` |
| 2 | `GET /courses/{id}` | Retrieve an existing course | `200 OK` |
| 3 | `POST /courses` | Create a valid course | `201 Created` or `200 OK` |
| 4 | `PUT /courses/{id}` | Update an existing course | `200 OK` |
| 5 | `DELETE /courses/{id}` | Delete an existing course | `200 OK` or `204 No Content` |
| 6 | `POST /courses` | Missing request body | `400 Bad Request` |
| 7 | `POST /courses` | Missing name field | `400 Bad Request` |
| 8 | `POST /courses` | Missing description field | `400 Bad Request` |
| 9 | `POST /courses` | Missing instructor field | `400 Bad Request` |
| 10 | `POST /courses` | Empty field values | `400 Bad Request` |
| 11 | `POST /courses` | Invalid JSON | `400 Bad Request` |
| 12 | `POST /courses` | Invalid data types | `400 Bad Request` |
| 13 | `GET /courses/{id}` | Course not found during GET | `404 Not Found` |
| 14 | `PUT /courses/{id}` | Course not found during PUT | `404 Not Found` |
| 15 | `DELETE /courses/{id}` | Course not found during DELETE | `404 Not Found` |
| 16 | `/courses/{id}` | Invalid course ID | `400 Bad Request` |
| 17 | Any API endpoint | Unsupported HTTP method | `405 Method Not Allowed` |
| 18 | `POST /courses` | Incorrect content type | `400 Bad Request` or `415 Unsupported Media Type` |