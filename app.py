
import os
import json
import sqlite3
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

from werkzeug.utils import secure_filename


app = Flask(__name__)


# ==========================================
# 1. APPLICATION CONFIGURATION
# ==========================================

DATABASE = os.path.abspath(
    os.environ.get("DATABASE_PATH", "responses.db")
)

UPLOAD_FOLDER = os.path.join(
    app.static_folder,
    "uploads"
)

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp"
}

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================
# 2. LOGIN DETAILS
# ==========================================

USERNAME = os.environ.get("APP_USERNAME", "admin")
PASSWORD = os.environ.get("APP_PASSWORD", "1234")


# ==========================================
# 3. DATABASE CONNECTION
# ==========================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================
# 4. DATABASE INITIALIZATION
# ==========================================

def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS responses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT,
            email TEXT,

            driving_styles TEXT,
            driving_preferences TEXT,
            passenger_preferences TEXT,

            profile_photo TEXT,
            license_photo TEXT,
            vehicle_photo TEXT,
            additional_photos TEXT

        )
    """)

    # Check existing database columns.

    existing_columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(responses)"
        ).fetchall()
    }

    # Add missing photograph columns to older databases.

    new_columns = {
        "profile_photo": "TEXT",
        "license_photo": "TEXT",
        "vehicle_photo": "TEXT",
        "additional_photos": "TEXT"
    }

    for column, data_type in new_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE responses ADD COLUMN {column} {data_type}"
            )

    conn.commit()
    conn.close()


# ==========================================
# 5. PHOTOGRAPH HANDLING
# ==========================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def save_photo(file):

    if not file or not file.filename:
        return None

    if not allowed_file(file.filename):
        return None

    original_name = secure_filename(file.filename)

    if not original_name or "." not in original_name:
        return None

    extension = original_name.rsplit(".", 1)[1].lower()

    unique_name = f"{uuid.uuid4().hex}.{extension}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_name
    )

    file.save(file_path)

    # Save the relative path in the database.

    return f"uploads/{unique_name}"


# ==========================================
# 6. LOGIN PAGE
# ==========================================

@app.route("/", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == USERNAME and password == PASSWORD:

            return redirect(url_for("home"))

        message = "Invalid username or password."

    return render_template(
        "login.html",
        message=message
    )


# ==========================================
# 7. HOME PAGE
# ==========================================

@app.route("/home")
def home():

    return render_template("home.html")


# ==========================================
# 8. SETTINGS PAGE
# ==========================================

@app.route("/settings")
@app.route("/settigs")
def settings():

    return render_template("settings.html")


# ==========================================
# 9. DRIVER DASHBOARD
# ==========================================

@app.route("/driver")
@app.route("/driver.html")
def driver():

    conn = get_db()

    try:

        respondents = conn.execute("""
            SELECT *
            FROM responses
            ORDER BY id DESC
        """).fetchall()

    finally:

        conn.close()

    # Convert database rows into dictionaries.

    respondents = [
        dict(row)
        for row in respondents
    ]

    # Convert additional photographs from JSON
    # strings into Python lists for driver.html.

    for respondent in respondents:

        try:

            respondent["additional_photos"] = json.loads(
                respondent.get("additional_photos") or "[]"
            )

            if not isinstance(
                respondent["additional_photos"], list
            ):
                respondent["additional_photos"] = []

        except (json.JSONDecodeError, TypeError):

            respondent["additional_photos"] = []

    return render_template(
        "driver.html",
        respondents=respondents
    )


# ==========================================
# 10. EXTERNAL QUESTIONNAIRE ENDPOINT
# ==========================================

@app.route("/receive", methods=["GET", "POST"])
def receive():

    # Allow direct browser testing.

    if request.method == "GET":

        return """
        <h2>QForm Endpoint Active</h2>
        <p>This endpoint is ready to receive questionnaire submissions.</p>
        <p>Submit your questionnaire using POST.</p>
        """

    # --------------------------------------
    # RESPONDENT DETAILS
    # --------------------------------------

    full_name = request.form.get(
        "full_name", ""
    ).strip()

    email = request.form.get(
        "email", ""
    ).strip()

    if not full_name or not email:

        return "Full name and email are required.", 400

    # --------------------------------------
    # QUESTIONNAIRE ANSWERS
    # --------------------------------------

    driving_styles = request.form.getlist("dstyles")

    driving_preferences = request.form.getlist("loves")

    passenger_preferences = request.form.getlist("passengers")

    # --------------------------------------
    # PHOTOGRAPH UPLOADS
    # --------------------------------------

    profile_photo = save_photo(
        request.files.get("profile_photo")
    )

    license_photo = save_photo(
        request.files.get("license_photo")
    )

    vehicle_photo = save_photo(
        request.files.get("vehicle_photo")
    )

    additional_files = request.files.getlist(
        "additional_photos"
    )

    additional_photos = []

    for photo in additional_files:

        saved_photo = save_photo(photo)

        if saved_photo:

            additional_photos.append(saved_photo)

    # --------------------------------------
    # SAVE RESPONDENT INFORMATION
    # --------------------------------------

    conn = get_db()

    try:

        conn.execute("""
            INSERT INTO responses (

                full_name,
                email,

                driving_styles,
                driving_preferences,
                passenger_preferences,

                profile_photo,
                license_photo,
                vehicle_photo,
                additional_photos

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            full_name,
            email,

            ", ".join(driving_styles),
            ", ".join(driving_preferences),
            ", ".join(passenger_preferences),

            profile_photo,
            license_photo,
            vehicle_photo,
            json.dumps(additional_photos)

        ))

        conn.commit()

    finally:

        conn.close()

    # --------------------------------------
    # REDIRECT TO DRIVER DASHBOARD
    # --------------------------------------

    return redirect(
        url_for("driver")
    )


# ==========================================
# 11. ERROR HANDLING
# ==========================================

@app.errorhandler(413)
def file_too_large(error):

    return (
        "Upload too large. Maximum request size is 16 MB.",
        413
    )


# ==========================================
# 12. START APPLICATION
# ==========================================

create_database()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )

