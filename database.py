from typing import List, Tuple

from psycopg2.extras import execute_values

Poll = Tuple[int, str, str]
Option = Tuple[int, str, int]
Vote = Tuple[str, int]
PollResults = Tuple[int, str, int, float]

CREATE_POLLS = """CREATE TABLE IF NOT EXISTS polls
(id SERIAL PRIMARY KEY, title TEXT, owner_username TEXT);"""
CREATE_OPTIONS = """CREATE TABLE IF NOT EXISTS options
(id SERIAL PRIMARY KEY, option_text TEXT, poll_id INTEGER, FOREIGN KEY(poll_id) REFERENCES polls (id));"""
CREATE_VOTES = """CREATE TABLE IF NOT EXISTS votes
(username TEXT, option_id INTEGER, FOREIGN KEY(option_id) REFERENCES options (id));"""
CREATE_VIEW_POLL_RESULTS = """CREATE VIEW poll_results AS
SELECT
    p.id AS poll_id,
    p.title AS poll_title,
    o.option_text,
    COUNT(v.option_id) AS vote_count,
    (COUNT(v.option_id) * 100.0 / SUM(COUNT(v.option_id)) OVER (PARTITION BY p.id)) AS vote_percentage
FROM polls p
JOIN options o ON p.id = o.poll_id
LEFT JOIN votes v ON o.id = v.option_id
GROUP BY p.id, p.title, o.option_text;
"""
SELECT_ALL_POLLS = "SELECT * FROM polls ORDER BY id DESC;"
SELECT_POLL = "SELECT * FROM polls WHERE id = %s;"
SELECT_POLL_WITH_RESULTS = """SELECT poll_title, option_text, vote_count, vote_percentage
FROM poll_results
WHERE poll_id = %s"""
SELECT_LATEST_POLL = """SELECT * FROM polls
JOIN options ON polls.id = options.poll_id
WHERE polls.id = (
    SELECT id FROM polls ORDER BY id DESC LIMIT 1
);"""
SELECT_POLL_OPTIONS = "SELECT * FROM options WHERE poll_id = %s;"
SELECT_OPTION = "SELECT * FROM options WHERE id = %s;"
SELECT_VOTES_FOR_OPTION = "SELECT * FROM votes WHERE option_id = %s;"

INSERT_POLL_RETURN_ID = "INSERT INTO polls (title, owner_username) VALUES (%s, %s) RETURNING id;"
INSERT_OPTION = "INSERT INTO options (option_text, poll_id) VALUES (%s, %s);"
INSERT_VOTE = "INSERT INTO votes (username, option_id) VALUES (%s, %s);"


def create_tables(connection):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_POLLS)
            cursor.execute(CREATE_OPTIONS)
            cursor.execute(CREATE_VOTES)
            # cursor.execute(CREATE_VIEW_POLL_RESULTS)


# -- polls --

def create_poll(connection, title: str, owner: str):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_POLL_RETURN_ID, (title, owner))

            poll_id = cursor.fetchone()[0]
            return poll_id


def get_latest_poll(connection) -> Poll:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_LATEST_POLL)
            return cursor.fetchall()


def get_poll(connection, poll_id: int) -> Poll:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_POLL, (poll_id,))
            return cursor.fetchone()


def get_poll_and_vote_results(connection, poll_id: int) -> List[PollResults]:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_POLL_WITH_RESULTS, (poll_id,))
            return cursor.fetchall()


def get_poll_options(connection, poll_id: int) -> List[Option]:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_POLL_OPTIONS, (poll_id,))
            return cursor.fetchall()


def get_polls(connection) -> List[Poll]:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_ALL_POLLS)
            return cursor.fetchall()


# -- options --


def add_option(connection, option_text: str, poll_id: int):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_OPTION, (option_text, poll_id))


def get_option(connection, option_id: int) -> Option:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_OPTION, (option_id,))
            return cursor.fetchone()


# -- votes --


def add_poll_vote(connection, username: str, option_id: int):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_VOTE, (username, option_id))


def get_votes_for_option(connection, option_id: int) -> List[Vote]:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_VOTES_FOR_OPTION, (option_id,))
            return cursor.fetchall()
