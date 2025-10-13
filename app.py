from models import db 
from flask import Flask , render_template, request, redirect, url_for, flash, jsonify, session
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def index():
    return '<h1>Welcome to CineLog</h1>'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)