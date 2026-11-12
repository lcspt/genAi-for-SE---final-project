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