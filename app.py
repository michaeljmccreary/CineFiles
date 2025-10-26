# Import statements to bring in features from other files and libraries
from config import Config
# Models is for database structure and interaction
from models import db, User
# Flask is for building the web application
from flask import Flask , render_template, request, redirect, url_for, flash, jsonify, session, g
# For catching database errors
import sqlite3
import os, time, random, requests
from dotenv import load_dotenv


# Create the Flask application and configure it
# Tells flask to look for templates and static files in the current directory
app = Flask(__name__) 
# Load configuration from Config class
app.config.from_object(Config)
# Hardocoded secret key for session management - Bad security makes app vulnerable to session attacks
# Secret key Generated using https://secretkeygen.vercel.app/ - hard coding into the app on purpose
app.secret_key = "46bcef3f322dec211634eb9d0f497056"
load_dotenv()
TMDB_API= os.environ.get("TMDB_API")
# Connect the database to the app
db.init_app(app)


#### ROUTES ####
# Home page route - when someone visits the root URL
@app.route('/')
def index():
    movie_list = get_movies()
    return render_template('index.html', movies = movie_list)
    

# User registration page - lets users create a new account
@app.route('/register', methods=['GET', 'POST'])
def register():
# If the form is submitted
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', "").strip()
        email = request.form.get('email', "").strip()
        # Password is plaintext - No hashing is done - Bad security
        password = request.form.get('password', "")
        # No lnegth checks or user input sanitisation 
        if not username or not email or not password:
            flash("Please submit all fields")
            return redirect(url_for("register"))
        # SQL Injection vulnerability here - user input is directly inserted into SQL query
        conn = sqlite3.connect('instance/cinefiles.db')
        cursor = conn.cursor()
        query = f"INSERT INTO user (username, email, password) VALUES ('{username}', '{email}', '{password}')"
        try:
            cursor.execute(query)
            conn.commit()
            flash("Account succsessfully created! Please log in to continue.")
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f"An error occurred: {e}")
            return redirect(url_for('register'))
    return render_template('Register.html')

# Login page - lets users log into their account if they have one
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Unsanitised user input - Bad security - Open to SQL Injection 
        email = request.form.get("email", "")
        # Password is in plaintext - No hashing is done - Bad security
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not email or not password:
            flash("Please enter both email and password")
            return redirect(url_for('login'))
        conn = sqlite3.connect('instance/cinefiles.db')
        cursor = conn.cursor()
        # Injected SQL statements will execute here 
        query = f"SELECT * FROM user WHERE email = '{email}'"
        try:
            cursor.execute(query)
            # Gets the record and if a password is found will return as plaintext
            result = cursor.fetchone()
            conn.close()
            # Plaintext password comparison - Bad security
            if result and result[3] == password:
                # Store user ID in session to keep user logged in
                session['user_id'] = result[0]
                session['username'] = result[1]
                # Make the session permanent so it lasts longer
                session.permanent = True  
                return redirect(url_for('profile'))
            else:
                flash("Invalid username or password")
                return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f"An error occurred: {e}")
            return redirect(url_for('login'))
    return render_template('Login.html')
            

# User profile page - shows user's information
@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to view your profile.")
        return redirect(url_for('login'))
    conn = sqlite3.connect('instance/cinefiles.db')
    cursor = conn.cursor()
    query = f"SELECT username, email FROM user WHERE id = {user_id}"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    if user:
        return render_template('Profile.html', username=user[0], email=user[1], movies=get_movies())
    else:
        flash("User not found.")
        return redirect(url_for('login'))
    
        

# Logout - logs the user out by clearing the session
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.")
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('query', '')
    # Build a simple HTML response to show the search query - Vulnerable to XSS attacks
    results_html = f"<h1>Search Results for '{query}'</h1>"
    return results_html

# function to get movies from the TMDB API and display them on the homepage 
def get_movies(count = 10, image_size = "w500"):
        url = "https://api.themoviedb.org/3/trending/movie/day"
        response = requests.get(url, params={"api_key": TMDB_API})
        response.raise_for_status()
        data = response.json()
        movies = []
        for movie in data["results"]:
            if len(movies) >= count:
                break
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/{image_size}{poster_path}" if poster_path else None
            movie_data = {
                "title": movie["title"],
                "release_date": movie["release_date"],
                "overview": movie["overview"],
                "poster_path": poster_url,
                "id": movie["id"],
                "vote_average": movie["vote_average"],
                "vote_count": movie["vote_count"]
            }
            movies.append(movie_data)
        return movies



if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        # Debug mode can expose errors and sensitive information - Bad security  
    app.run(debug=True)






        