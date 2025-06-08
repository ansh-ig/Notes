# app.py
from flask import Flask, render_template,flash, request, session, redirect, url_for
import sqlite3
from cs50 import SQL
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required
import requests
from functools import wraps



app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///notes.db")

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('notes.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Initialize the database
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == "POST":
        # Get form data
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check if username and password are provided
        if not username:
            return apology("must provide username", 400)
        if not password:
            return apology("must provide password", 400)
        if not confirmation:
            return apology("must provide confirmation", 400)

        # Check if passwords match
        if password != confirmation:
            return apology("passwords do not match", 400)

        # Hash the password
        hash = generate_password_hash(password)

        # Try to insert the new user into the database
        try:
            new_user_id = db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                username, hash
            )
        except:
            return apology("username already exists", 400)

        # Log the user in
        session["user_id"] = new_user_id

        # Redirect to homepage
        return redirect("/")

    # Handle GET request to render the registration form
    else:
        return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Login successful!", "success")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    """Log user out"""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/login")


@app.route("/pass", methods=["GET", "POST"])
@login_required
def change_pass():
    """Change password"""
    if request.method == "POST":
        # Get form data
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Check if new passwords match
        if new_password != confirm_password:
            return apology("Passwords do not match", 403)

        # Query database for the current user based on session user_id
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Check if the query returned any rows and user exists
        if rows is None or len(rows) != 1:
            return apology("User not found", 403)

        # Verify that the current password matches the hashed password in the database
        if not check_password_hash(rows[0]["hash"], current_password):
            return apology("Invalid current password", 403)

        # Hash the new password
        hash = generate_password_hash(new_password)

        # Update the user's password in the database
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hash, session["user_id"])

        # Flash success message and redirect to homepage
        flash("Password updated successfully!")
        return redirect("/")

    else:
        # Render the change password form for GET requests
        return render_template("pass.html")

# Initialize the database


def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    conn.close()


# Home route to display all notes
@app.route('/')
@login_required
def index():
    search_query = request.args.get('q', '')
    user_id = session["user_id"]

    conn = get_db_connection()

    # If there's a search query, filter notes by it and user_id
    if search_query:
        notes = conn.execute("SELECT id, text FROM notes WHERE user_id = ? AND text LIKE ?",
                             (user_id, '%' + search_query + '%')).fetchall()
    else:
        notes = conn.execute("SELECT id, text FROM notes WHERE user_id = ?", (user_id,)).fetchall()

    conn.close()

    return render_template('index.html', notes=notes)

 # Pass the whole notes object

# Route to add a new note


@app.route('/create', methods=['POST'])
@login_required
def create_note():
    note_text = request.form.get('note')
    user_id = session["user_id"]  # Get the user_id from the session

    if note_text:
        conn = get_db_connection()
        conn.execute('INSERT INTO notes (text, user_id) VALUES (?, ?)', (note_text, user_id))
        conn.commit()
        conn.close()

    return redirect(url_for('index'))

# Route to delete a note


@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_note(id):
    user_id = session["user_id"]

    conn = get_db_connection()
    # Ensure the note belongs to the logged-in user before deleting
    conn.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', (id, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


# Route to update an existing note

@app.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_note(id):
    note_text = request.form.get('note')
    user_id = session["user_id"]

    if note_text:
        conn = get_db_connection()
        # Ensure that the note belongs to the logged-in user
        conn.execute('UPDATE notes SET text = ? WHERE id = ? AND user_id = ?', (note_text, id, user_id))
        conn.commit()
        conn.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)


# CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL);
# CREATE UNIQUE INDEX username ON users (username);
