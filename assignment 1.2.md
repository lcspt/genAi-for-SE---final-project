create the complete Python Flask code for app.py with these requirements: 
1. Create a Flask REST API with all CRUD operations for courses 
2. Store data in a JSON file called "courses.json" 
3. Include these endpoints: 
- POST /api/courses 
- Add a new course 
- GET /api/courses 
- Get all courses 
- GET /api/courses/ 
- Get a specific course 
- PUT /api/courses/ 
- Update a course 
- DELETE /api/courses/ 
- Delete a course 
4. Each course must have: 
- id (auto-generated, starting from 1) 
- name (required) 
- description (required) 
- target_date (required, format YYYY-MM-DD) 
- status (required), must be: 
"Not Started", 
"In Progress", 
"Completed") 
- created_at (auto-generated timestamp) 
5. Include proper error handling for: - Missing required fields - Course not found - Invalid status values - File read/write errors 
6. Add significant comments throughout the code
7. Make sure the app creates courses.json automatically if it doesn't exist

Give output in a markdown file, i will paste it in the IDE


# CodeCraftHub Flask REST API

This project provides a Flask REST API for managing courses.

## Features

- Full CRUD operations
- JSON file storage using `courses.json`
- Automatic course ID generation
- Required field validation
- Date format validation
- Status validation
- Automatic file creation
- Error handling for missing courses and file errors

## API Endpoints

|
 Method 
|
 Endpoint 
|
 Description 
|
|
---
|
---
|
---
|
|
`POST`
|
`/api/courses`
|
 Add a new course 
|
|
`GET`
|
`/api/courses`
|
 Get all courses 
|
|
`GET`
|
`/api/courses/<id>`
|
 Get a specific course 
|
|
`PUT`
|
`/api/courses/<id>`
|
 Update a course 
|
|
`DELETE`
|
`/api/courses/<id>`
|
 Delete a course 
|

## Project Structure

```text
codecrafthub/
├── app.py
└── courses.json
```

The application automatically creates `courses.json` if it does not already exist.

## Complete `app.py`

```python
"""
CodeCraftHub Course REST API

This Flask application provides CRUD operations for courses.

Data is stored in a local JSON file named courses.json.
No database or authentication is required.

Run the application with:

    uv run python app.py

Or, if the virtual environment is activated:

    python app.py
"""

from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

import json
import os
import tempfile

from flask import Flask, jsonify, request


# -----------------------------------------------------------------------------
# Flask application setup
# -----------------------------------------------------------------------------

app = Flask(__name__)


# -----------------------------------------------------------------------------
# File and application configuration
# -----------------------------------------------------------------------------

# Store courses.json in the same directory as this app.py file.
# This prevents the file location from depending on the directory from which
# the application is started.
BASE_DIR = Path(__file__).resolve().parent
COURSES_FILE = BASE_DIR / "courses.json"

# A lock prevents two requests from reading or writing the JSON file at the
# exact same time within this application process.
FILE_LOCK = Lock()

# These are the only valid values allowed for a course status.
VALID_STATUSES = {
    "Not Started",
    "In Progress",
    "Completed",
}


# -----------------------------------------------------------------------------
# Custom exception
# -----------------------------------------------------------------------------

class CourseFileError(Exception):
    """
    Custom exception used when courses.json cannot be read or written.

    This allows route handlers to return a clear JSON error response instead
    of exposing a Python traceback to the API client.
    """

    pass


# -----------------------------------------------------------------------------
# JSON file helper functions
# -----------------------------------------------------------------------------

def ensure_courses_file() -> None:
    """
    Create courses.json automatically if it does not exist.

    The file starts with an empty JSON array because courses are stored as a
    list of objects.
    """

    try:
        if not COURSES_FILE.exists():
            COURSES_FILE.write_text("[]\n", encoding="utf-8")
    except OSError as error:
        raise CourseFileError(
            f"Unable to create {COURSES_FILE.name}: {error}"
        ) from error


def read_courses() -> list[dict[str, Any]]:
    """
    Read and return all courses from courses.json.

    Returns:
        A list of course dictionaries.

    Raises:
        CourseFileError: If the file cannot be created, read, or parsed.
    """

    ensure_courses_file()

    try:
        with FILE_LOCK:
            file_contents = COURSES_FILE.read_text(encoding="utf-8")

            # Convert the JSON text into a Python object.
            courses = json.loads(file_contents)

    except json.JSONDecodeError as error:
        raise CourseFileError(
            f"{COURSES_FILE.name} contains invalid JSON: {error}"
        ) from error

    except OSError as error:
        raise CourseFileError(
            f"Unable to read {COURSES_FILE.name}: {error}"
        ) from error

    # The JSON file must contain a list of courses.
    if not isinstance(courses, list):
        raise CourseFileError(
            f"{COURSES_FILE.name} must contain a JSON array."
        )

    return courses


def write_courses(courses: list[dict[str, Any]]) -> None:
    """
    Write all courses to courses.json.

    A temporary file is written first, then moved into place. This reduces the
    risk of leaving courses.json partially written if an error occurs while
    saving data.

    Args:
        courses: The complete list of course dictionaries.

    Raises:
        CourseFileError: If the file cannot be written.
    """

    try:
        with FILE_LOCK:
            # Create a temporary file in the same directory as courses.json.
            # Using the same directory allows os.replace() to be atomic.
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=BASE_DIR,
                prefix="courses_",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:

                json.dump(
                    courses,
                    temporary_file,
                    indent=2,
                    ensure_ascii=False,
                )

                temporary_file.write("\n")
                temporary_file_path = temporary_file.name

            # Replace the original file with the completed temporary file.
            os.replace(temporary_file_path, COURSES_FILE)

    except OSError as error:
        # If an error occurs, attempt to remove the temporary file.
        if "temporary_file_path" in locals():
            try:
                Path(temporary_file_path).unlink(missing_ok=True)
            except OSError:
                pass

        raise CourseFileError(
            f"Unable to write {COURSES_FILE.name}: {error}"
        ) from error


# -----------------------------------------------------------------------------
# Validation helper functions
# -----------------------------------------------------------------------------

def validate_course_payload(
    payload: Any,
    partial_update: bool = False,
) -> tuple[dict[str, str] | None, str | None]:
    """
    Validate the JSON body sent by the client.

    Args:
        payload: The decoded JSON request body.
        partial_update:
            - False for POST and normal full PUT validation.
            - True if partial updates should be allowed.

    Returns:
        A tuple containing:
            - Cleaned course data, or None if validation fails.
            - Error message, or None if validation succeeds.
    """

    # The request body must be a JSON object.
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    # These are the only fields clients are allowed to submit.
    allowed_fields = {
        "name",
        "description",
        "target_date",
        "status",
    }

    unexpected_fields = set(payload.keys()) - allowed_fields

    if unexpected_fields:
        fields = ", ".join(sorted(unexpected_fields))
        return None, f"Unexpected field(s): {fields}."

    # All four fields are required when creating a course or performing a
    # complete PUT update.
    required_fields = {
        "name",
        "description",
        "target_date",
        "status",
    }

    if not partial_update:
        missing_fields = required_fields - set(payload.keys())

        if missing_fields:
            fields = ", ".join(sorted(missing_fields))
            return None, f"Missing required field(s): {fields}."

    # Validate the name field if it was provided.
    if "name" in payload:
        if not isinstance(payload["name"], str):
            return None, "The 'name' field must be a string."

        if not payload["name"].strip():
            return None, "The 'name' field is required."

    # Validate the description field if it was provided.
    if "description" in payload:
        if not isinstance(payload["description"], str):
            return None, "The 'description' field must be a string."

        if not payload["description"].strip():
            return None, "The 'description' field is required."

    # Validate the target_date field if it was provided.
    if "target_date" in payload:
        if not isinstance(payload["target_date"], str):
            return None, "The 'target_date' field must be a string."

        try:
            # This confirms that the date uses the YYYY-MM-DD format.
            datetime.strptime(payload["target_date"], "%Y-%m-%d")

        except ValueError:
            return None, (
                "The 'target_date' field must use YYYY-MM-DD format."
            )

    # Validate the status field if it was provided.
    if "status" in payload:
        if payload["status"] not in VALID_STATUSES:
            valid_values = ", ".join(sorted(VALID_STATUSES))

            return None, (
                f"Invalid status. Allowed values are: {valid_values}."
            )

    # Strip unnecessary whitespace from text values before saving.
    cleaned_data: dict[str, str] = {}

    for field in ("name", "description", "target_date", "status"):
        if field in payload:
            cleaned_data[field] = payload[field].strip()

    return cleaned_data, None


def get_next_course_id(courses: list[dict[str, Any]]) -> int:
    """
    Generate the next course ID.

    The first course receives ID 1. Future courses receive one more than the
    highest existing ID.
    """

    if not courses:
        return 1

    existing_ids = [
        course["id"]
        for course in courses
        if isinstance(course.get("id"), int)
    ]

    if not existing_ids:
        return 1

    return max(existing_ids) + 1


def find_course_by_id(
    courses: list[dict[str, Any]],
    course_id: int,
) -> dict[str, Any] | None:
    """
    Find one course by its numeric ID.

    Returns:
        The matching course dictionary, or None if it does not exist.
    """

    for course in courses:
        if course.get("id") == course_id:
            return course

    return None


# -----------------------------------------------------------------------------
# API routes
# -----------------------------------------------------------------------------

@app.post("/api/courses")
def create_course():
    """
    Create a new course.

    Expected request body:

    {
        "name": "Learn Flask",
        "description": "Build REST APIs with Flask",
        "target_date": "2026-12-31",
        "status": "Not Started"
    }
    """

    # Parse the request body as JSON.
    payload = request.get_json(silent=True)

    if payload is None:
        return jsonify({
            "error": "Request body must contain valid JSON."
        }), 400

    # Validate all required course fields.
    course_data, validation_error = validate_course_payload(payload)

    if validation_error:
        return jsonify({
            "error": validation_error
        }), 400

    try:
        courses = read_courses()

        # Build the new course object.
        new_course = {
            "id": get_next_course_id(courses),
            "name": course_data["name"],
            "description": course_data["description"],
            "target_date": course_data["target_date"],
            "status": course_data["status"],
            "created_at": datetime.now().astimezone().isoformat(),
        }

        courses.append(new_course)
        write_courses(courses)

    except CourseFileError as error:
        return jsonify({
            "error": str(error)
        }), 500

    return jsonify(new_course), 201


@app.get("/api/courses")
def get_all_courses():
    """
    Return all courses.

    Example response:

    [
        {
            "id": 1,
            "name": "Learn Flask",
            "description": "Build REST APIs with Flask",
            "target_date": "2026-12-31",
            "status": "Not Started",
            "created_at": "2026-11-12T12:00:00+00:00"
        }
    ]
    """

    try:
        courses = read_courses()

    except CourseFileError as error:
        return jsonify({
            "error": str(error)
        }), 500

    return jsonify(courses), 200


@app.get("/api/courses/<int:course_id>")
def get_specific_course(course_id: int):
    """
    Return one course by ID.

    Example:
        GET /api/courses/1
    """

    try:
        courses = read_courses()

    except CourseFileError as error:
        return jsonify({
            "error": str(error)
        }), 500

    course = find_course_by_id(courses, course_id)

    if course is None:
        return jsonify({
            "error": f"Course with ID {course_id} was not found."
        }), 404

    return jsonify(course), 200


@app.put("/api/courses/<int:course_id>")
def update_course(course_id: int):
    """
    Replace an existing course.

    PUT requires all editable fields:

    {
        "name": "Updated course name",
        "description": "Updated description",
        "target_date": "2026-12-31",
        "status": "In Progress"
    }

    The ID and created_at values are generated by the server and cannot be
    changed by the client.
    """

    payload = request.get_json(silent=True)

    if payload is None:
        return jsonify({
            "error": "Request body must contain valid JSON."
        }), 400

    # PUT is treated as a complete replacement, so all required fields must
    # be present.
    course_data, validation_error = validate_course_payload(payload)

    if validation_error:
        return jsonify({
            "error": validation_error
        }), 400

    try:
        courses = read_courses()

    except CourseFileError as error:
        return jsonify({
            "error": str(error)
        }), 500

    course = find_course_by_id(courses, course_id)

    if course is None:
        return jsonify({
            "error": f"Course with ID {course_id} was not found."
        }), 404

    # Keep the original ID and creation timestamp.
    original_created_at = course["created_at"]

    # Replace the editable fields with the validated values.
    course.update({
        "name": course_data["name"],
        "description": course_data["description"],
        "target_date": course_data["target_date"],
        "status": course_data["status"],
        "created_at": original_created_at,
    })

    try:
        write_courses(courses)

    except CourseFileError as error:
        return jsonify({
            "error": str(error)
        }), 500

    return jsonify(course), 200


@app.delete("/api/courses/<int:course_id>")
def delete_course(course_id: int):
    """
    Delete a course by ID.

    Example:
        DELETE /api/courses/1
    """

    try:
        courses = read_courses()

    except CourseFileError as error:
        return jsonify({
            "error": str(error)
        }), 500

    course = find_course_by_id(courses, course_id)

    if course is None:
        return jsonify({
            "error": f"Course with ID {course_id} was not found."
        }), 404

    # Remove the matching course from the list.
    courses.remove(course)

    try:
        write_courses(courses)

    except CourseFileError as error:
        return jsonify({
            "error": str(error)
        }), 500

    return jsonify({
        "message": f"Course with ID {course_id} was deleted successfully.",
        "course": course,
    }), 200


# -----------------------------------------------------------------------------
# Error handlers
# -----------------------------------------------------------------------------

@app.errorhandler(404)
def handle_not_found(error):
    """
    Return a JSON response for unknown routes.

    This also handles requests to endpoints that do not exist.
    """

    return jsonify({
        "error": "The requested endpoint was not found."
    }), 404


@app.errorhandler(405)
def handle_method_not_allowed(error):
    """
    Return a JSON response when an unsupported HTTP method is used.
    """

    return jsonify({
        "error": "The HTTP method is not allowed for this endpoint."
    }), 405


@app.errorhandler(500)
def handle_internal_server_error(error):
    """
    Return a JSON response for unexpected server errors.

    Detailed tracebacks should be viewed in the development server console,
    not returned to API clients.
    """

    return jsonify({
        "error": "An unexpected internal server error occurred."
    }), 500


# -----------------------------------------------------------------------------
# Application entry point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Ensure the JSON file exists before the server starts.
    ensure_courses_file()

    # Debug mode is useful during development.
    # Do not use debug=True in a production deployment.
    app.run(debug=True)
```

## Install Flask with `uv`

From the project directory:

```bash
uv add Flask
```

## Run the application

```bash
uv run python app.py
```

The API will be available at:

```text
http://127.0.0.1:5000
```

## Example POST request

```bash
curl -X POST http://127.0.0.1:5000/api/courses \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Learn Flask REST APIs",
    "description": "Learn how to build REST APIs with Python and Flask.",
    "target_date": "2026-12-31",
    "status": "Not Started"
  }'
```

## Example GET requests

Get all courses:

```bash
curl http://127.0.0.1:5000/api/courses
```

Get one course:

```bash
curl http://127.0.0.1:5000/api/courses/1
```

## Example PUT request

```bash
curl -X PUT http://127.0.0.1:5000/api/courses/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Learn Flask REST APIs",
    "description": "Build and test REST APIs with Flask.",
    "target_date": "2026-12-31",
    "status": "In Progress"
  }'
```

## Example DELETE request

```bash
curl -X DELETE http://127.0.0.1:5000/api/courses/1
```