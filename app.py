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

# Search route - allows users to search for movies
@app.route('/search')
def search():
    # Get the search query from the URL parameters - Vulnerable to XSS attacks
    query = request.args.get('query', '')
    # Build a simple HTML response to show the search query - Vulnerable to XSS attacks
    url = f"https://api.themoviedb.org/3/search/movie"
    response = requests.get(url, params={"api_key": TMDB_API, "query": query})
    # Check for request errors
    response.raise_for_status()
    # Get the JSON data from the response
    data = response.json()
    # Render the search results template with the movies found
    return render_template('search.html', movies=data["results"], query=query)

# function to get movies from the TMDB API and display them on the homepage 
def get_movies(count = 10, image_size = "w500"):
        # Fetch trending movies from TMDB API
        url = "https://api.themoviedb.org/3/trending/movie/day"
        response = requests.get(url, params={"api_key": TMDB_API})
        # Check for request errors
        response.raise_for_status()
        # Get the JSON data from the response
        data = response.json()
        # Process and return a list of movies
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

# Add Movie Details Route
@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    # Fetch movie details from TMDB API
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(url, params={"api_key": TMDB_API})
    response.raise_for_status()
    movie = response.json()
    # Get poster image for the movie
    poster_path = movie.get("poster_path")
    # Build full poster URL
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    movie_data = {
        "title": movie["title"],
        "release_date": movie["release_date"],
        "overview": movie["overview"],
        "poster_path": poster_url,
        "id": movie["id"],
        "vote_average": movie["vote_average"],
        "vote_count": movie["vote_count"]
    }
    return render_template('movie.html', movie=movie_data)

# Route to add a review for a movie
@app.route('/movie/<int:movie_id>/review', methods=['POST'])
def add_review(movie_id):
    # Get user ID from session
    user_id = session.get('user_id')
    # If user is not logged in, redirect to login page
    if not user_id:
        flash("Please log in to add a review.")
        return redirect(url_for('login'))
    # Get review data from form
    rating = request.form.get('rating')
    comment = request.form.get('comment', "")
    # Check if there is a rating
    if not rating:
        flash("Please provide a rating.")
        return redirect(url_for('movie_details', movie_id=movie_id))
    # Direct database connection using sqlite3 - allows for SQL injection
    conn = sqlite3.connect('instance/cinefiles.db')
    cursor = conn.cursor()
    query = f"INSERT INTO review (movie_id, rating, comment, user_id) VALUES ({movie_id}, {rating}, '{comment}', {user_id})"
    try:
        cursor.execute(query)
        conn.commit()
        flash("Review added successfully!")
    except sqlite3.Error as e:
        flash(f"An error occurred: {e}")
    finally:
        conn.close()
    return redirect(url_for('movie_details', movie_id=movie_id))

# Route to add a comment to a movie discussion
@app.route('/movie/<int:movie_id>/comment', methods=['POST'])
def add_comment(movie_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to add a comment.")
        return redirect(url_for('login'))
    # Get comment content from form
    content = request.form.get('content', "")
    if not content:
        flash("Please provide comment content.")
        return redirect(url_for('movie_details', movie_id=movie_id))
    
# Route to add a reply to a comment
@app.route('/movie/<int:movie_id>/reply', methods=['POST'])
def add_reply(movie_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to add a reply.")
        return redirect(url_for('login'))
    content = request.form.get('content', "")
    if not content:
        flash("Please provide reply content.")
        return redirect(url_for('movie_details', movie_id=movie_id))


if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        # Debug mode can expose errors and sensitive information - Bad security  
    app.run(debug=True)






        