

from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# DATABASE CONFIGURATION
DATABASE = "responses.db"


# CREATE DATABASE AND TABLE
def create_database():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT,
            driving_styles TEXT,
            driving_preferences TEXT,
            passenger_preferences TEXT
        )
    """)

    conn.commit()
    conn.close()


# DATABASE CONNECTION
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# EXISTING SUBMIT ROUTE
@app.route("/submit", methods=["POST"])
def submit():
    return "Your form has been submitted!"


# LOGIN DETAILS
USERNAME = "admin"
PASSWORD = "1234"


# LOGIN PAGE
@app.route("/", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == USERNAME and password == PASSWORD:
            return redirect(url_for("home"))

        else:
            message = "Invalid username or password."

    return render_template("login.html", message=message)


# HOME PAGE
@app.route("/home")
def home():
    return render_template("home.html")


# SETTINGS PAGE
@app.route("/settigs")
def settings():
    return render_template("settings.html")


# DRIVER DASHBOARD
@app.route("/driver.html")
def driver():

    conn = get_db()

    respondents = conn.execute(
        "SELECT * FROM responses ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "driver.html",
        respondents=respondents
    )


# RECEIVE EXTERNAL QUESTIONNAIRE DATA
@app.route("/receive", methods=["POST"])
def receive():

    # Respondent details
    full_name = request.form.get("full_name", "")
    email = request.form.get("email", "")

    # Questionnaire answers
    driving_styles = request.form.getlist("dstyles")
    driving_preferences = request.form.getlist("loves")
    passenger_preferences = request.form.getlist("passengers")

    # Save information in database
    conn = get_db()

    conn.execute("""
        INSERT INTO responses (
            full_name,
            email,
            driving_styles,
            driving_preferences,
            passenger_preferences
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        full_name,
        email,
        ", ".join(driving_styles),
        ", ".join(driving_preferences),
        ", ".join(passenger_preferences)
    ))

    conn.commit()
    conn.close()

    # Redirect to driver dashboard
    return redirect(url_for("driver"))


# RUN APPLICATION


create_database()

if __name__ == "__main__":

    app.run(debug=True)

