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
# An attacker can hijack or forge sessions if they know the secret key
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
            # This will expose database errors to a an attacker - Bad security
            flash(f"Database error: {str(e)} | Query: {query}")
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
        if not email or not password:
            flash("Please enter both email and password")
            return redirect(url_for('login'))
        conn = sqlite3.connect('instance/cinefiles.db')
        cursor = conn.cursor()
        # Injected SQL statements will execute here - Modified for full authentication bypass vulnerability
        query = f"SELECT * FROM user WHERE email = '{email}' AND password = '{password}'"
        try:
            cursor.execute(query)
            # Fetch result - If row returned, login succeeds (allows bypass via injection)
            result = cursor.fetchone()
            conn.close()
            if result:
                # Store user ID in session to keep user logged in
                # I should use session.regenerate() here to prevent session fixation attacks
                session['user_id'] = result[0]
                session['username'] = result[1]
                # Make the session permanent so it lasts longer
                session.permanent = True  
                return redirect(url_for('profile'))
            else:
                flash("Invalid username or password")
                return redirect(url_for('login'))
        except sqlite3.Error as e:
            # Expose database errors to show SQL injection is possible
            flash(f"Database error: {str(e)} | Query: {query}")
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
    query = f"SELECT username, email, bio, location FROM user WHERE id = {user_id}"
    cursor.execute(query)
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
        # Get the data - No sanitisation or validation - Vulnerable to XSS attacks
        bio = request.form.get('bio', "")
        location = request.form.get('location', "")
        # Update the user's profile with unsanitised input - Vulnerable to SQL Injection
        conn = sqlite3.connect('instance/cinefiles.db')
        cursor = conn.cursor()
        query = f"UPDATE user SET bio = '{bio}', location = '{location}' WHERE id = {user_id}"
        try:
            cursor.execute(query)
            conn.commit()
            flash("Profile updated successfully!")
        except sqlite3.Error as e:
            flash(f"An error occurred: {e}")
        finally:
            conn.close()
        return redirect(url_for('profile'))
    
# GET request - show profile wth the updated information 
    conn = sqlite3.connect('instance/cinefiles.db')
    cursor = conn.cursor()
    query = f"SELECT username, email, bio, location FROM user WHERE id = {user_id}"
    cursor.execute(query)
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
    query = f"SELECT review.id, review.movie_id, review.rating, review.comment, review.user_id, user.username FROM review JOIN user ON review.user_id = user.id WHERE review.movie_id = {movie_id}"
    cursor.execute(query)
    reviews = cursor.fetchall()
    
    # Fetch any existing comments for the movie with username
    query = f"SELECT comment.id, comment.post_id, comment.user_id, comment.content, user.username FROM comment JOIN user ON comment.user_id = user.id WHERE comment.post_id = {movie_id}"
    cursor.execute(query)
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
    # Insert comment into database
    conn = sqlite3.connect('instance/cinefiles.db')
    cursor = conn.cursor()
    query = f"INSERT INTO comment (post_id, user_id, content) VALUES ({movie_id}, {user_id}, '{content}')"
    try:
        cursor.execute(query)
        conn.commit()
        flash("Comment added successfully!")
    except sqlite3.Error as e:
        flash(f"An error occurred: {e}")
    finally:
        conn.close()
    return redirect(url_for('movie_details', movie_id=movie_id))

# Run the application
if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        # Propagate exceptions causes detailed error messages to be shown - Bad security
        app.config['PROPAGATE_EXCEPTIONS'] = True
        # Debug mode can expose errors and sensitive information - Bad security  
    app.run(debug=True)






        