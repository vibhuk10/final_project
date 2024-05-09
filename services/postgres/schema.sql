CREATE EXTENSION postgis;

\set ON_ERROR_STOP on

SET max_parallel_maintenance_workers TO 80;
SET maintenance_work_mem TO '16 GB';

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

CREATE INDEX rum_tweets ON tweets USING rum(to_tsvector('english', text));
CREATE INDEX get_tweets ON tweets(created_at, id_tweets, id_users, text, id_urls);
CREATE INDEX urls_null ON tweets (id_urls) WHERE id_urls IS NULL;

COMMIT;

