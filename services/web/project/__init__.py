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
import bleach
from math import ceil


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
    res = connection.execute(sql, {'last_tweet_id': last_tweet_id})
    for row in res.fetchall():
        tweets.append({
            'username': row[0],
            'text': row[1],
            'created_at': row[2],
            'url':row[3]
        })
    return tweets

def get_tweets_search(query, page_num):
    messages = []
    offset = (page_num - 1) * 20
    sql = sqlalchemy.sql.text("""
    SELECT id_tweets,
    ts_headline('english', text, plainto_tsquery(:query), 'StartSel=<span> StopSel=</span>') AS highlighted_text,
    created_at,
    id_users
    FROM tweets
    WHERE to_tsvector('english', text) @@ plainto_tsquery(:query)
    ORDER BY created_at DESC
    LIMIT 20 OFFSET :offset;
""")

    res = connection.execute(sql, {'query': ' & '.join(query.split()), 'offset': offset})
    for row in res.fetchall():
        user_sql = sqlalchemy.sql.text("""
            SELECT username
            FROM users
            WHERE id_users = :id_users;
        """)
        user_res = connection.execute(user_sql, {'id_users': row[3]})
        user_row = user_res.fetchone()
        messages.append({
            'username': user_row[0],
            'text': bleach.clean(row[1], tags=['p', 'br', 'a', 'b', 'span'], attributes={'a': ['href']}).replace("<span>", "<span class=highlight>"),
            'created_at': row[2]
        })

    return messages

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

        
@app.route("/login", methods=['GET', 'POST'])
def login():
    username = request.cookies.get('username')
    password = request.cookies.get('password')

    if check_login(username, password):
        return redirect('/')

    username = request.form.get('username')
    password = request.form.get('password')

    if username is None:
        return render_template('login.html', bad_credentials=False)

    else:
        if not check_login(username, password):
            return render_template('login.html', bad_credentials=True)
        else:
            response = make_response(redirect('/'))
            response.set_cookie('username', username)
            response.set_cookie('password', password)
            return response

@app.route("/logout")
def logout():
    response = make_response(render_template('logout.html'))
    response.delete_cookie('username')
    response.delete_cookie('password')
    return response

@app.route("/create_account", methods=['GET', 'POST'])
def create_account():
    username = request.cookies.get('username')
    password = request.cookies.get('password')

    if check_login(username, password):
        return redirect('/')

    username_input = request.form.get('username_input')
    password_input = request.form.get('password_input')
    password_confirm_input = request.form.get('password_confirm_input')

    if username_input is None:
        return render_template('create_account.html')
    elif not username_input or not password_input:
        return render_template('create_account.html', missing_value=True)
    else:
        if password_input != password_confirm_input:
            return render_template('create_account.html', pass_not_match=True)
        else:
            try:
                #with connection.begin() as trans:
                    sql = sqlalchemy.sql.text('''
                        INSERT INTO users (username, password)
                        VALUES (:username, :password)
                    ''')

                    res = connection.execute(sql, {
                        'username': username_input,
                        'password': password_input
                    })

                    print(res)

                    response = make_response(redirect('/'))
                    response.set_cookie('username', username_input)
                    response.set_cookie('password', password_input)
                    return response
            except sqlalchemy.exc.IntegrityError:
                return render_template('create_account.html', exists=True)

@app.route("/create_message", methods=['GET', 'POST'])
def create_message():
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    
    isLoggedIn = check_login(username, password)
    if not isLoggedIn:
        return redirect('/')

    message = request.form.get('message')
    
    if not message:
        return render_template('create_message.html', invalid=True, logged_in=isLoggedIn)
    try:
        #with connection.begin() as trans:
            sql = sqlalchemy.sql.text('''
                SELECT id_users FROM users
                WHERE username = :username AND password = :password;
            ''')

            res = connection.execute(sql, {
                'username': username,
                'password': password
            })

            for row in res.fetchall():
                user_id = row[0]
        
            sql = sqlalchemy.sql.text('''
                SELECT tweet_urls.id_urls
                FROM tweet_urls
                LEFT JOIN tweets on tweet_urls.id_urls = tweets.id_urls 
                WHERE tweets.id_urls IS NULL
                ORDER BY random()
                LIMIT 1;
            ''')

            res = connection.execute(sql)

            for row in res.fetchall():
                id_url = row[0]

            sql = sqlalchemy.sql.text("""
                INSERT INTO tweets (id_users,id_urls,text,created_at) VALUES (:id_users,:id_urls,:text,:created_at);
            """)
            res = connection.execute(sql, {
                'id_users': user_id,
                'id_urls': id_url,
                'text': message, 
                'created_at': str(datetime.datetime.now()).split('.')[0]
            })
            
    except sqlalchemy.exc.SQLAlchemyError as e:
        return render_template('create_message.html', invalid=True, logged_in=isLoggedIn)
    else:
        return render_template('create_message.html', message_sent=True, logged_in=isLoggedIn)    

@app.route("/search", methods=['GET', 'POST'])
def search():
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    
    isLoggedIn = check_login(username, password)

    messages = []
    message = ""

    page_num = int(request.args.get('page', 1))
    query = request.args.get('query', '')

    if query:
        messages = get_tweets_search(query, page_num)
    else:
        messages = get_tweets(page_num)

    response = make_response(render_template('search.html', messages=messages, logged_in=isLoggedIn, username=username, page_num=page_num, query=query))

    return response
