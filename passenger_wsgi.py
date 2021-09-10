import sys, os
import json
import datetime
import re
from pprint import pprint

# Print Databases
from queue import Queue

# Flask
import sqlite3
from flask import Flask, render_template, redirect, url_for, jsonify, request, g
import flask

# Flask Login
from model.users import Users
import flask_login
from flask_login import LoginManager, login_required, login_user, logout_user

application = Flask(__name__)
application.secret_key = open("supersecret.key").read()

users = Users("./db/users.json", application)


@application.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


### LOGIN MANAGER
login_manager = flask_login.LoginManager()
login_manager.init_app(application)

# This function is just to set a session timer.
@application.before_request
def before_request():
    flask.session.permanent = True
    application.permanent_session_lifetime = datetime.timedelta(minutes=20)
    flask.session.modified = True


@login_manager.user_loader
def user_loader(username):
    return users.find_user(username)


@application.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return flask.render_template("pw.html")
    if request.method == "POST":
        # Login and validate the user.
        # user should be an instance of your `User` class
        if "username" not in flask.request.form:
            flask.redirect(flask.url_for("indexPage"))

        username = flask.request.form["username"]
        pw = flask.request.form["password"]

        print(f"{username}: {pw}")
        auth_user = users.try_login_user(username, pw)

        if auth_user:
            login_user(auth_user)

        return flask.redirect(url_for("indexPage"))


@login_manager.unauthorized_handler
def unauthorized_handler():
    return flask.redirect(url_for("login"))


@application.route("/protected")
@flask_login.login_required
def protected():
    return (
        "Logged in as: "
        + flask_login.current_user.id
        + ":"
        + users.find_user(flask_login.current_user.id).password_hash
    )


@application.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("indexPage"))


@application.route("/")
def indexPage():
    return render_template("visitor_signin.html", prideMonth=True)


@application.route("/successful")
def t1():
    pageData = {}
    # pageData should contain their name, their NetID, their 'division', and their membership types.
    return render_template("signedIn.html", prideMonth=True, pageData={})


@application.route("/denied")
def deniedAccess():
    return render_template(
        "access_denied.html", prideMonth=True, deniedType="cardNotFound"
    )


@application.route("/api/checkSignin", methods=["POST"])
def apiT1():
    print(request.form.to_dict())
    return redirect(url_for("t1"))


create_table_users = """
CREATE TABLE IF NOT EXISTS users ( 
	rums_pk INT PRIMARY KEY,
   	netid VARCHAR(20),
	email VARCHAR(50) NOT NULL,
	name VARCHAR(50) NOT NULL,
	zk_pk INT UNQIUE
);

"""

create_table_cards = """
CREATE TABLE IF NOT EXISTS cards ( 
	rums_pk INT PRIMARY KEY,
	card_no VARCHAR(20) NOT NULL
);

"""

create_table_memberships = """
CREATE TABLE IF NOT EXISTS memberships ( 
	membership_pk INT PRIMARY KEY,
   	rums_pk INT,
	start_date DATETIME NOT NULL,
	end_date DATETIME,
	human_name VARCHAR(20)
);

"""


create_table_visits = """
CREATE TABLE IF NOT EXISTS visits ( 
	visits_pk INT PRIMARY KEY,
   	rums_pk INT NOT NULL,
	card_no VARCHAR(20) NOT NULL,
	entry_time DATETIME NOT NULL,
	exit_time DATETIME,
	granted INT NOT NULL
);

"""

create_table_group_memberships = """
CREATE TABLE IF NOT EXISTS group_memberships ( 
	group_membership_pk INT PRIMARY KEY,
	group_mem_name VARCHAR(20),
	start_date DATETIME NOT NULL,
	end_date DATETIME,
	admin_user_pk INT
);

"""

create_table_group_member_users = """
CREATE TABLE IF NOT EXISTS group_members ( 
	group_member_pk INT PRIMARY KEY,
	group_membership_pk INT NOT NULL,
	rums_pk INT NOT NULL
);

"""

tabLES = [
    create_table_group_member_users,
    create_table_cards,
    create_table_group_memberships,
    create_table_visits,
    create_table_users,
    create_table_memberships,
]

from db.sqlite_store import *


@application.route("/admin/", methods=["GET", "POST"])
@login_required
def admPage():
    for tableDat in tabLES:
        query_db(tableDat)
    return render_template("admin.html", prideMonth=True)
