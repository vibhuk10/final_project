CREATE EXTENSION postgis;

\set ON_ERROR_STOP on

BEGIN;


CREATE TABLE users (
    id_users BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE tweet_urls (
    id_urls BIGSERIAL PRIMARY KEY,
    url TEXT
);

CREATE TABLE tweets (
    id_tweets BIGSERIAL PRIMARY KEY,
    id_users BIGINT NOT NULL REFERENCES users(id_users),
    id_urls BIGINT NOT NULL UNIQUE REFERENCES tweet_urls(id_urls),
    text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);


COMMIT;

