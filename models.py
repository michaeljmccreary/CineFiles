# IMport statemets
# Flask-SQLAlchemy for the database models and interactions
from flask_sqlalchemy import SQLAlchemy
# Uswing sqlite3 for raw sql queries - allows for SQL injection 
import _sqlite3
# Creates the database
db = SQLAlchemy()
# User class represents users in the database
class User(db.Model):
    # Primary key for SQL database, will auto increment with each new user
    id = db.Column(db.Integer, primary_key=True)
    # Username field, could be vulberable to XSS if not properly sanitised
    username = db.Column(db.String(30), unique=True, nullable=False)
    # Email is stored in plaintext, no encryption or hashing - Bad security
    email = db.Column(db.String(60), unique=True, nullable=False)
    # Sroting password in plaintext - No hashing or encryption - Bad security
    password = db.Column(db.String(50), nullable=False)
    reviews = db.relationship('Review', backref='author', lazy=True)

    # Sets the user's password in plaintext - No hashing or encryption - Bad security
    def set_password(self, password):
        self.password == password

    # Checks the provided password against the stored password
    # Plaintext comparison - No hashing or encryption - Bad security
    # Vulnerable to rainbow table and brute force attack
    def check_password(self, password):
        return self.password == password
    
    # This class is for forum posts
    class Post(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100), nullable=False)
        content = db.Column(db.Text, nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        timestamp = db.Column(db.DateTime, index=True, default=db.func.now())        

    class Review(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        movie_id = db.Column(db.Integer, nullable=False)
        rating = db.Column(db.Integer, nullable=False)
        comment = db.Column(db.Text, nullable=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        timestamp = db.Column(db.DateTime, index=True, default=db.func.now())

        # Method to add a review to the database
        # Unsanitised user input - SQL Injection vulnerability
        def add_review(self, movie_id, rating, comment, user_id):
            # Direct database connection using sqlite3 - allows for SQL injection
            conn = _sqlite3.connect('instance/cinefiles.db')
            cursor = conn.cursor()
            query = f"INSERT INTO review (movie_id, rating, comment, user_id) VALUES ({movie_id}, {rating}, '{comment}', {user_id})"
            try:
                cursor.execute(query)
                conn.commit()
                return True
            except _sqlite3.Error as e:
                print(f"An error occurred: {e}")
                return False
            
    class Comment(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        content = db.Column(db.Text, nullable=False)
        timestamp = db.Column(db.DateTime, index=True, default=db.func.now())

    class Reply(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        content = db.Column(db.Text, nullable=False)
        timestamp = db.Column(db.DateTime, index=True, default=db.func.now())