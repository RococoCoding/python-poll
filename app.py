from flask import Flask, render_template, request, redirect
import os
from psycopg2.errors import DivisionByZero
from dotenv import load_dotenv
import database
from models.poll import Poll
from connection_pool import get_connection


app = Flask(__name__)

# Set up the database connection
DATABASE_PROMPT = "Enter the DATABASE_URI value or leave empty to load from .env file: "
load_dotenv()
with get_connection() as create_connection:
    database.create_tables(create_connection)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create_poll", methods=["GET", "POST"])
def create_poll():
    if request.method == "POST":
        poll_title = request.form.get("poll_title")
        poll_owner = request.form.get("poll_owner")
        poll = Poll(poll_title, poll_owner)
        poll.save()

        option_keys = [key for key in request.form if key.startswith("option_")]

        for key in option_keys:
            option = request.form.get(key)
            if option:
                poll.add_option(option)

        return redirect("/polls")
    return render_template("create_poll.html")


@app.route("/polls")
def polls():
    returned_polls = Poll.all()
    return render_template("polls.html", polls=returned_polls)


@app.route("/vote/<int:poll_id>", methods=["GET", "POST"])
def vote(poll_id: int):
    if request.method == "POST":
        option_id = request.form.get("option_id")
        username = request.form.get("username")
        with get_connection() as connection:
            database.add_poll_vote(connection, username, option_id)
            return redirect("/polls")

    poll_options = Poll.get(poll_id).options
    return render_template("vote.html", poll_id=poll_id, options=poll_options)


@app.route("/poll_results/<int:poll_id>")
def poll_results(poll_id: int):
    try:
        with get_connection() as connection:
            poll_and_votes = database.get_poll_and_vote_results(connection, poll_id) or []
            poll_title = poll_title=poll_and_votes[0][0]
    except (DivisionByZero, IndexError):
        poll_and_votes = []
    return render_template("poll_results.html", poll_id=poll_id, poll_title=poll_title, results=poll_and_votes)


if __name__ == "__main__":
    app.run()
