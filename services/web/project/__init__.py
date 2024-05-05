import os

from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    render_template,
    redirect,
    url_for,
    make_response,
    session,
    flash
)
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy import text, create_engine
import psycopg2
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import re


app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)

engine = sqlalchemy.create_engine("postgresql://postgres:pass@postgres:5432", connect_args={
    'application_name': '__init__.py',
    })
connection = engine.connect()

def check_login(username, password):
    sql = sqlalchemy.sql.text('''
        SELECT username FROM users WHERE username = :username AND password = :password;
        ''')

    res = connection.execute(sql, {
        'username': username,
        'password': password
    })

    if res.fetchone() is not None:
        return True
    else:
        return False

def get_tweets(page_num):
    tweets = []
    sql = sqlalchemy.sql.text("""
        SELECT users.username, tweets.text, tweets.created_at, tweet_urls.url
        FROM tweets
        JOIN users USING (id_users)
        JOIN tweet_urls USING (id_urls)
        WHERE tweets.id_tweets > :last_tweet_id
        ORDER BY tweets.created_at DESC
        LIMIT 20;
    """)
    last_tweet_id = (page_num - 1) * 20  # Assuming tweet IDs are sequential
    page = connection.execute(sql, {'last_tweet_id': last_tweet_id})
    for row in page.fetchall():
        tweets.append({
            'username': row[0],
            'text': row[1],
            'created_at': row[2]
        })
    return tweets

@app.route("/")
def root():
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    
    isLoggedIn = False
    
    if check_login(username, password):
        isLoggedIn = True

    page_num = int(request.args.get('page', 1))
    tweets = get_tweets(page_num)

    return render_template('root.html', logged_in=isLoggedIn, page_num=page_num, username=username,tweets=tweets)

        
#@app.route("/login")

#@app.route("/logout")

#@app.route("/create_account")

#@app.route("/create_message")

#@app.route("/search")

