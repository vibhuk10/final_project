import argparse
import sqlalchemy
import random
import string

parser = argparse.ArgumentParser()
parser.add_argument('--db',required=True)
args = parser.parse_args()

# create database connection
engine = sqlalchemy.create_engine(args.db, connect_args={
    'application_name': 'load_data.py',
    })
connection = engine.connect()

#includes letters
def create_random_word(length):
    characters = string.ascii_letters
    word = ''.join(random.choice(characters) for _ in range(length))
    return word    

#includes letters and numbers
def create_random_word2(length):
    characters = string.ascii_letters + string.digits
    word = ''.join(random.choice(characters) for _ in range(length))
    return word 

def create_users(length):
    for i in range(length):
        sql = sqlalchemy.sql.text("""
        INSERT INTO users (username, password) VALUES (:username, :password);
        """)
        try:
            res = connection.execute(sql, {
                'username': create_random_word2(random.randint(8, 12)),
                'password': create_random_word2(random.randint(8, 12))
                })
        except sqlalchemy.exc.IntegrityError as e:
            print("user",i,"FAIL",e)

def create_urls(length):
    for i in range(length):
        sql = sqlalchemy.sql.text("""
        INSERT INTO tweet_urls (url) VALUES (:url);
        """)
        try:
            res = connection.execute(sql, {
                'url': create_random_word2(random.randint(13, 17)),
                })
        except sqlalchemy.exc.IntegrityError as e:
            print("url",i,"FAIL",e)

def create_tweets(length):
    # get user ids
    sql = sqlalchemy.sql.text("""
    SELECT id_users FROM users;
    """)
    res = connection.execute(sql)
    user_ids = [tup[0] for tup in res.fetchall()]
        
    # get url ids    
    sql = sqlalchemy.sql.text("""
    SELECT id_urls FROM tweet_urls;
    """)
    res = connection.execute(sql)
    url_ids = [tup[0] for tup in res.fetchall()]

    for i in range(length):
        chosen_url_id =  random.choice(url_ids)
        url_ids.remove(chosen_url_id)

        sql = sqlalchemy.sql.text("""
        INSERT INTO tweets (id_users, id_urls, text) VALUES (:id_users, :id_urls, :text);
        """)
        try:
            res = connection.execute(sql, {
                'id_users': random.choice(user_ids),
                'id_urls': chosen_url_id,
                'text': create_random_word2(random.randint(20, 40))
                })
        except sqlalchemy.exc.IntegrityError as e:
            print("tweet",i,"FAIL",e)

create_users(50)
create_urls(50)
create_tweets(50)

connection.close()
