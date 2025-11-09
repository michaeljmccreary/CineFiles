# Import statements to bring in features from other files and libraries
from config import Config
# Models is for database structure and interaction
from models import db, User
# Flask is for building the web application
from flask import Flask , render_template, request, redirect, url_for, flash, jsonify, session, g
# For catching database errors
import sqlite3
# For password hashing
import bcrypt
# For sanitizing user input to prevent XSS attacks
import html
# For logging errors
import logging
# For regular expressions to validate input formats
import re
import os, time, random, requests
# For handling time-related tasks
from datetime import timedelta
# To load environment variables from a .env file
from dotenv import load_dotenv
# For rate limiting to prevent brute force attacks
from flask_limiter import Limiter
# Function to get the remote address of the client
from flask_limiter.util import get_remote_address

# Load environment variables from .env file
load_dotenv()
# Create the Flask application and configure it
# Tells flask to look for templates and static files in the current directory
app = Flask(__name__) 
# Set session lifetime to 15 minutes for better security
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
# Load configuration from Config class
app.config.from_object(Config)

# Secret key is now being stored in the .env file for better security
app.secret_key = os.getenv('secret_key')
TMDB_API= os.environ.get("TMDB_API")
# Connect the database to the app
db.init_app(app)

# Initialize Flask-Limiter with the app and set default rate limits
# This prevents against brute force attacks 
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "50 per hour"],
    storage_uri="memory://"
)

#### HELPER FUNCTIONS - to increase security####

# Validates an email for format
def validate_email(email):
    # Regular expression for validating an email address
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    # returns true if email is valid or false if it is not
    return re.match(email_pattern, email) 

# validates the strength of a password
def validate_password_strength(password):
    # check the minimum lenth
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter.")
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter.")
    # Check for at least one digit
    if not re.search(r'[0-9]', password):
        raise ValueError("Password must contain at least one digit.")
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>]).")
    

# sanitises user input to prevent XSS attacks
def sanitize_input(user_input):
    return html.escape(user_input).strip()

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
        username = sanitize_input(request.form.get('username', ""))
        email = sanitize_input(request.form.get('email', ""))
        # Password is now encrypted using bcrypt
        password = request.form.get('password', "").strip()
        confirm_password = request.form.get('confirm_password', "").strip()
        # adding validation to check if passwords match
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("register"))
        
        # validation to ensure all fields are filled in 
        if not username or not email or not password:
            flash("Please submit all fields")
            return redirect(url_for("register"))
        
        # length checks for username and password
        if len(username) < 5 or len(password) < 8:
            flash("Username must be at least 5 characters and password at least 8 characters long.")
            return redirect(url_for("register"))
        
        # Check that username only contains alphanumeric characters and underscores - prevents XSS attacks
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash("Username can only contain letters, numbers, and underscores")
            return redirect(url_for("register"))
        
        # Validate email format
        if not validate_email(email):
            flash("Please enter a valid email address")
            return redirect(url_for("register"))
        
        # Validate password strength
        try:
            validate_password_strength(password)
        except ValueError as ve:
            flash(str(ve))
            return redirect(url_for("register"))
        
        # Hash the password with bcrypt
        hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = sqlite3.connect('instance/cinefiles.db')
        cursor = conn.cursor()
        # Using parameterized queries to prevent SQL injection        
        query = "INSERT INTO user (username, email, password) VALUES (?, ?, ?)"
        try:
            cursor.execute(query, (username, email, hash_password))
            conn.commit()
            flash("Account succsessfully created! Please log in to continue.")
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            flash("An error occurred")
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('Register.html')

# Login page - lets users log into their account if they have one
@app.route('/login', methods=['GET', 'POST'])
# Rate limiting to prevent brute force attacks
@limiter.limit("5 per minute")  
def login():
    if request.method == 'POST':
        # Get form data
        email = sanitize_input(request.form.get("email", ""))
        # Password is now being hashing
        password = request.form.get("password", "").strip()
        # validation to ensure both fields are filled in
        if not email or not password:
            flash("Please enter both email and password")
            return redirect(url_for('login'))
        
        # validation to check email format to prevent SQL injection attacks
        if not validate_email(email):
            flash("Please enter a valid email address")
            return redirect(url_for('login'))
        
        # connect to the database
        conn = sqlite3.connect('instance/cinefiles.db')
        cursor = conn.cursor()
    # Using parameterized queries to prevent SQL injection  
        query = "SELECT id, username, password FROM user WHERE email = ?"
        try:
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            conn.close()
            # Password comparison using bcrypt - compares hashed password with stored hash
            if result and bcrypt.checkpw(password.encode('utf-8'), result[2].encode('utf-8')):
                # Set session variables
                # prevents session fixation attacks by clearing any existing session data
                session.clear()
                session['user_id'] = result[0]
                session['username'] = result[1]
                session.permanent = True  
                return redirect(url_for('profile'))
            else:
                flash("Invalid username or password")
                return redirect(url_for('login'))
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            flash("An error occurred. Please try again.")
            return redirect(url_for('login'))
    return render_template('Login.html')
            

# User profile page - shows user's information
@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    # Check if user is logged in
    if not user_id:
        flash("Please log in to view your profile.")
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('instance/cinefiles.db')
    cursor = conn.cursor()
    # Using parameterized queries to prevent SQL injection
    query = "SELECT username, email, bio, location FROM user WHERE id = ?"
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return render_template('Profile.html', username=user[0], email=user[1], bio=user[2], location=user[3], movies=get_movies())
    else:
        flash("User not found.")
        return redirect(url_for('login'))

    
# Edit profile route - Will allow users to update their profiles 
@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    # Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to edit your profile.")
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Get the data - sanitisation is now being completed
        bio = sanitize_input(request.form.get('bio', ""))
        location = sanitize_input(request.form.get('location', ""))

        # validation to check length of bio and location
        if len(bio) > 500:
            flash("Bio cannot exceed 500 characters.")
            return redirect(url_for('edit_profile'))
        if len(location) > 30:
            flash("Location cannot exceed 30 characters.")
            return redirect(url_for('edit_profile'))
        
        # Update the user's profile with sanitized input - prevents SQL injection
        conn = sqlite3.connect('instance/cinefiles.db')
        cursor = conn.cursor()
        query = "UPDATE user SET bio = ?, location = ? WHERE id = ?"
        try:
            cursor.execute(query, (bio, location, user_id))
            conn.commit()
            flash("Profile updated successfully!")
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            flash("An error occurred. Please try again.")
        finally:
            conn.close()
        return redirect(url_for('profile'))
    
# GET request - show profile wth the updated information 
    conn = sqlite3.connect('instance/cinefiles.db')
    cursor = conn.cursor()
    query = "SELECT username, email, bio, location FROM user WHERE id = ?"
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return render_template('edit_profile.html', username=user[0], email=user[1], bio=user[2], location=user[3])
    else:
        flash("User not found.")
        return redirect(url_for('login'))

    

# Logout - logs the user out by clearing the session
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('index'))

# Search route - allows users to search for movies
@app.route('/search')
def search():
    query = request.args.get('query', '').strip()

    # sanitize the query to prevent XSS attacks
    safe_query = sanitize_input(query)

    # validation to check if query is empty
    if not safe_query:
        flash("Please enter a search query.")
        return redirect(url_for('index'))
    
    url = f"https://api.themoviedb.org/3/search/movie"
    response = requests.get(url, params={"api_key": TMDB_API, "query": safe_query})
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
    response = requests.get(url, params={"api_key": TMDB_API, "append_to_response": "credits"})
    response.raise_for_status()
    movie = response.json()
    # Get poster image for the movie
    poster_path = movie.get("poster_path")
    # Build full poster URL
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    
    # Get genres
    genres = ", ".join([genre["name"] for genre in movie.get("genres", [])])
    
    # Get director from credits
    director = "N/A"
    if "credits" in movie and "crew" in movie["credits"]:
        for crew_member in movie["credits"]["crew"]:
            if crew_member.get("job") == "Director":
                director = crew_member.get("name", "N/A")
                break
    
    # Get cast
    cast = "N/A"
    if "credits" in movie and "cast" in movie["credits"]:
        cast_list = [actor["name"] for actor in movie["credits"]["cast"][:5]]
        cast = ", ".join(cast_list) if cast_list else "N/A"
    
    movie_data = {
        "title": movie["title"],
        "release_date": movie.get("release_date", "N/A"),
        "overview": movie.get("overview", "No overview available"),
        "poster_url": poster_url,
        "id": movie["id"],
        "vote_average": movie.get("vote_average", 0),
        "vote_count": movie.get("vote_count", 0),
        "genre": genres,
        "director": director,
        "cast": cast
    }
    # Fetch any existing reviews for the movie with username
    conn = sqlite3.connect('instance/cinefiles.db')
    cursor = conn.cursor()
    query = "SELECT review.id, review.movie_id, review.rating, review.comment, review.user_id, user.username FROM review JOIN user ON review.user_id = user.id WHERE review.movie_id = ?"
    cursor.execute(query, (movie_id,))
    reviews = cursor.fetchall()
    
    # Fetch any existing comments for the movie with username
    query = "SELECT comment.id, comment.post_id, comment.user_id, comment.content, user.username FROM comment JOIN user ON comment.user_id = user.id WHERE comment.post_id = ?"
    cursor.execute(query, (movie_id,))
    comments = cursor.fetchall()
    conn.close()

    return render_template('movie.html', movie=movie_data, reviews=reviews, comments=comments)

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
    comment = html.escape(request.form.get('comment', "")).strip()
    # Check if there is a rating
    if not rating:
        flash("Please provide a rating.")
        return redirect(url_for('movie_details', movie_id=movie_id))
    
    # adding validation to ensure rating is between 1 and 10
    try:
        rating = int(rating)
        if rating < 1 or rating > 10:
            flash("Rating must be between 1 and 10.")
            return redirect(url_for('movie_details', movie_id=movie_id))
    except ValueError:
        flash("Invalid rating value.")
        return redirect(url_for('movie_details', movie_id=movie_id)) 

    # Direct database connection using sqlite3 - prevents SQL injection with parameterized queries
    conn = sqlite3.connect('instance/cinefiles.db')
    cursor = conn.cursor()
    query = "INSERT INTO review (movie_id, rating, comment, user_id) VALUES (?, ?, ?, ?)"
    try:
        cursor.execute(query, (movie_id, rating, comment, user_id))

        conn.commit()
        flash("Review added successfully!")
    except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            flash("An error occurred. Please try again.")
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
    content = html.escape(request.form.get('content', "")).strip()
    if not content:
        flash("Please provide comment content.")
        return redirect(url_for('movie_details', movie_id=movie_id))
    # Insert comment into database
    conn = sqlite3.connect('instance/cinefiles.db')
    cursor = conn.cursor()
    query = "INSERT INTO comment (post_id, user_id, content) VALUES (?, ?, ?)"
    try:
        cursor.execute(query, (movie_id, user_id, content))

        conn.commit()
        flash("Comment added successfully!")
    except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            flash("An error occurred. Please try again.")
    finally:
        conn.close()
    return redirect(url_for('movie_details', movie_id=movie_id))

# Run the application
if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        # making propagate exceptions false to prevent detailed error messages being shown to attakers 
        app.config['PROPAGATE_EXCEPTIONS'] = False
        # Debug mode will only be anbled now in developert mode 
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'True'
    app.run(debug=debug_mode)
