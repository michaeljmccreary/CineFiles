# Import statements to bring in features from other files and libraries
from config import Config
# Models is for database structure and interaction
from models import db, User
# Flask is for building the web application
from flask import Flask , render_template, request, redirect, url_for, flash, jsonify, session, g
# For catching database errors
import sqlite3

# Create the Flask application and configure it
# Tells flask to look for templates and static files in the current directory
app = Flask(__name__) 
# Load configuration from Config class
app.config.from_object(Config)
# Hardocoded secret key for session management - Bad security makes app vulnerable to session attacks
app.secret_key = "46bcef3f322dec211634eb9d0f497056"
# Connect the database to the app
db.init_app(app)


#### ROUTES ####
# Home page route - when someone visits the root URL
@app.route('/')
def index():
    return render_template('index.html')

# User registration page - lets users create a new account
@app.route('/register', methods=['GET', 'POST'])
def register():
# If the form is submitted
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', "").strip()
        email = request.form.get('email', "").strip()
        password = request.form.get('password', "")

    
        # If already exists, redirect to register page
        if db.session.query(db.exists().where(models.User.username == username)).scalar():
            flash('Username already exists!')
            return redirect(url_for('register'))
        new_user = models.User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account Succsessfully Created! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = models.User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)