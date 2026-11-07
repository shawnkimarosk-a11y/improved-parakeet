
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route("/submit", methods=["POST"])
def submit():
    return "Your form has been submitted!"





# Login details
USERNAME = "admin"
PASSWORD = "1234"


# Login page
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


# Home page
@app.route("/home")
def home():
    return render_template("home.html")

# Settings page
@app.route("/settigs")
def settings():
    return render_template("settings.html")


# driver page pick
@app.route("/driver.html")
def driver():
    return render_template("driver.html")
     
# 4.Receive form data
@app.route("/receive", methods=["POST"])
def receive():

     # Respondent details
    full_name = request.form.get("full_name", "")
    email = request.form.get("email", "")

    # Questionnaire answers
    driving_styles = request.form.getlist("dstyles")
    driving_preferences = request.form.getlist("loves")
    passenger_preferences = request.form.getlist("passengers")

    #Send information to driver.html
    return render_template(
        "driver.html",
        full_name=full_name,
        email=email,
        driving_styles=driving_styles,
        driving_preferences=driving_preferences,
        passenger_preferences=passenger_preferences
    )
    





# Run the application
if __name__ == "__main__":
    app.run(debug=True)
