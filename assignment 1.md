Create a simple personalized learning platform called CodeCraftHub where developers can track courses they want to learn. 
Requirements: 
- Use Python with Flask framework 
- Store course data in a simple JSON text file (NO database needed) 
- No authentication or user management needed 
- Focus on learning REST API basics Each course should track the following: 
    - Course name - Description - Target completion date - Current status (Not Started, In Progress, Completed) 
Recommend: 
1. A simple project structure for beginners 
2. The REST API endpoints to be created 
3. How to store and retrieve data from a JSON file

CodeCraftHub.md
# CodeCraftHub

CodeCraftHub is a beginner-friendly Flask REST API for tracking courses using a JSON text file instead of a database.

## Features

- Create courses
- View all courses
- View an individual course
- Update course details
- Delete courses
- Filter courses by status
- Store data in a simple JSON file
- No authentication or user management

## 1. Recommended project structure

```text
codecrafthub/
├── app.py
├── requirements.txt
└── data/
    └── courses.json
```

Create `data/courses.json` with:

```json
[]
```

## 2. Installation

Create and activate a virtual environment:

```bash
python -m venv venv
```

macOS/Linux:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

Install Flask:

```bash
pip install -r requirements.txt
```

## 3. Requirements file

Create `requirements.txt`:

```text
Flask>=3.0.0
```

## 2 / 3 . With uv do

```bash
mkdir codecrafthub
cd codecrafthub

uv python install 3.14.4
uv init --python 3.14.4
uv add Flask
```

This creates a pyproject.toml
file and a virtual environment managed by uv

## 4. Flask application

Create `app.py`:

```python
from datetime import date
from pathlib import Path
from threading import Lock
import json
import os
import tempfile

from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "courses.json"
FILE_LOCK = Lock()

VALID_STATUSES = {
    "Not Started",
    "In Progress",
    "Completed",
}


def ensure_data_file():
    """Create the data directory and JSON file if they do not exist."""
    DATA_DIR.mkdir(exist_ok=True)

    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def read_courses():
    """Read all courses from the JSON file."""
    ensure_data_file()

    with FILE_LOCK:
        try:
            content = DATA_FILE.read_text(encoding="utf-8")
            return json.loads(content)
        except json.JSONDecodeError:
            return []


def write_courses(courses):
    """
    Write courses to the JSON file.

    A temporary file is used so the original file is not partially
    overwritten if the application stops during a write.
    """
    ensure_data_file()

    with FILE_LOCK:
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=DATA_DIR,
            encoding="utf-8"
        ) as temp_file:
            json.dump(courses, temp_file, indent=2)
            temp_file.write("\n")
            temp_file_path = temp_file.name

        os.replace(temp_file_path, DATA_FILE)


def validate_course_data(data, partial=False):
    """Validate and normalize course input."""
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."

    allowed_fields = {
        "course_name",
        "description",
        "target_completion_date",
        "current_status",
    }

    unknown_fields = set(data.keys()) - allowed_fields

    if unknown_fields:
        return None, f"Unknown fields: {', '.join(sorted(unknown_fields))}"

    required_fields = {
        "course_name",
        "description",
        "target_completion_date",
    }

    if not partial:
        missing_fields = required_fields - set(data.keys())

        if missing_fields:
            return None, (
                "Missing required fields: "
                + ", ".join(sorted(missing_fields))
            )

    if "course_name" in data:
        if (
            not isinstance(data["course_name"], str)
            or not data["course_name"].strip()
        ):
            return None, "course_name must be a non-empty string."

    if "description" in data:
        if not isinstance(data["description"], str):
            return None, "description must be a string."

    if "target_completion_date" in data:
        if not isinstance(data["target_completion_date"], str):
            return None, "target_completion_date must be a string."

        try:
            date.fromisoformat(data["target_completion_date"])
        except ValueError:
            return None, (
                "target_completion_date must use YYYY-MM-DD format."
            )

    if "current_status" in data:
        if data["current_status"] not in VALID_STATUSES:
            return None, (
                "current_status must be one of: "
                + ", ".join(sorted(VALID_STATUSES))
            )

    cleaned_data = {}

    for field in allowed_fields:
        if field in data:
            value = data[field]

            cleaned_data[field] = (
                value.strip()
                if isinstance(value, str)
                else value
            )

    return cleaned_data, None


def get_next_id(courses):
    """Generate the next numeric course ID."""
    if not courses:
        return 1

    return max(course["id"] for course in courses) + 1


@app.get("/")
def home():
    return jsonify({
        "name": "CodeCraftHub",
        "message": "Course tracking REST API",
        "documentation": {
            "courses": "/api/courses"
        }
    })


@app.get("/api/courses")
def list_courses():
    """
    Get all courses.

    Optional filter:
    GET /api/courses?status=In%20Progress
    """
    courses = read_courses()
    status_filter = request.args.get("status")

    if status_filter:
        if status_filter not in VALID_STATUSES:
            return jsonify({
                "error": "Invalid status filter."
            }), 400

        courses = [
            course
            for course in courses
            if course["current_status"] == status_filter
        ]

    return jsonify(courses), 200


@app.post("/api/courses")
def create_course():
    """Create a new course."""
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "Request body must contain valid JSON."
        }), 400

    cleaned_data, error = validate_course_data(data)

    if error:
        return jsonify({"error": error}), 400

    cleaned_data.setdefault("current_status", "Not Started")

    courses = read_courses()

    new_course = {
        "id": get_next_id(courses),
        **cleaned_data
    }

    courses.append(new_course)
    write_courses(courses)

    return jsonify(new_course), 201


@app.get("/api/courses/<int:course_id>")
def get_course(course_id):
    """Get one course by ID."""
    courses = read_courses()

    course = next(
        (course for course in courses if course["id"] == course_id),
        None
    )

    if course is None:
        return jsonify({"error": "Course not found."}), 404

    return jsonify(course), 200


@app.patch("/api/courses/<int:course_id>")
def update_course(course_id):
    """Partially update a course."""
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "Request body must contain valid JSON."
        }), 400

    cleaned_data, error = validate_course_data(data, partial=True)

    if error:
        return jsonify({"error": error}), 400

    courses = read_courses()

    course = next(
        (course for course in courses if course["id"] == course_id),
        None
    )

    if course is None:
        return jsonify({"error": "Course not found."}), 404

    course.update(cleaned_data)
    write_courses(courses)

    return jsonify(course), 200


@app.delete("/api/courses/<int:course_id>")
def delete_course(course_id):
    """Delete a course."""
    courses = read_courses()

    course = next(
        (course for course in courses if course["id"] == course_id),
        None
    )

    if course is None:
        return jsonify({"error": "Course not found."}), 404

    courses.remove(course)
    write_courses(courses)

    return jsonify({
        "message": "Course deleted successfully.",
        "course": course
    }), 200


if __name__ == "__main__":
    ensure_data_file()
    app.run(debug=True)
```

## 5. Run the application

```bash
python app.py
```

The API will be available at:

```text
http://127.0.0.1:5000
```

## 6. Course data format

Each course contains:

- `id`
- `course_name`
- `description`
- `target_completion_date`
- `current_status`

Example:

```json
{
  "id": 1,
  "course_name": "REST API Design with Flask",
  "description": "Learn how to build REST APIs using Python and Flask.",
  "target_completion_date": "2026-12-15",
  "current_status": "In Progress"
}

{
  "id": 2,
  "course_name": "Generative AI: Elevate your Software Development Career, Final Project",
  "description": "consolidate your learning by engaging with a comprehensive project that challenges you to build a personalized learning platform for developers using generative AI.",
  "target_completion_date": "2026-11-15",
  "current_status": "In Progress"
}
```

Valid statuses:

```text
Not Started
In Progress
Completed
```

Target completion dates must use:

```text
YYYY-MM-DD
```

## 7. REST API endpoints

|
 Method 
|
 Endpoint 
|
 Purpose 
|
|
---
|
---
|
---
|
|
`GET`
|
`/api/courses`
|
 List all courses 
|
|
`GET`
|
`/api/courses?status=In%20Progress`
|
 Filter courses by status 
|
|
`GET`
|
`/api/courses/<id>`
|
 Get one course 
|
|
`POST`
|
`/api/courses`
|
 Create a course 
|
|
`PATCH`
|
`/api/courses/<id>`
|
 Update one or more fields 
|
|
`DELETE`
|
`/api/courses/<id>`
|
 Delete a course 
|

## 8. API examples

### Create a course

```bash
curl -X POST http://127.0.0.1:5000/api/courses \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "REST API Design with Flask",
    "description": "Learn how to build REST APIs using Python and Flask.",
    "target_completion_date": "2026-12-15",
    "current_status": "Not Started"
  }'

curl -X POST http://127.0.0.1:5000/api/courses \
  -H "Content-Type: application/json" \
  -d '{
  "course_name": "Generative AI: Elevate your Software Development Career, Final Project",
  "description": "consolidate your learning by engaging with a comprehensive project that challenges you to build a personalized learning platform for developers using generative AI.",
  "target_completion_date": "2026-11-15",
  "current_status": "In Progress"
  }'
```

### Retrieve all courses

```bash
curl http://127.0.0.1:5000/api/courses
```

### Retrieve one course

```bash
curl http://127.0.0.1:5000/api/courses/1
```

### Filter courses by status

```bash
curl "http://127.0.0.1:5000/api/courses?status=In%20Progress"
```

### Update a course

```bash
curl -X PATCH http://127.0.0.1:5000/api/courses/1 \
  -H "Content-Type: application/json" \
  -d '{
    "current_status": "In Progress"
  }'
```

### Mark a course as completed

```bash
curl -X PATCH http://127.0.0.1:5000/api/courses/1 \
  -H "Content-Type: application/json" \
  -d '{
    "current_status": "Completed"
  }'
```

### Delete a course

```bash
curl -X DELETE http://127.0.0.1:5000/api/courses/1
```

## 9. How JSON storage works

The application uses two helper functions.

### Reading data

```python
courses = read_courses()
```

This reads `data/courses.json`, parses the JSON into a Python list, and returns the courses.

### Writing data

```python
write_courses(courses)
```

This converts the Python list back into formatted JSON and saves it to `data/courses.json`.

Example file contents:

```json
[
  {
    "id": 1,
    "course_name": "REST API Design with Flask",
    "description": "Learn how to build REST APIs using Python and Flask.",
    "target_completion_date": "2026-12-15",
    "current_status": "Not Started"
  }
]
```

## 10. Notes

JSON file storage is suitable for learning and small personal projects. For a production or multi-user application, a database would be more reliable because JSON files are not ideal for:

- Large amounts of data
- Concurrent writes
- Multiple users
- Advanced searching
- Transactions and data integrity