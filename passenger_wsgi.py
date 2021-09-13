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

#Datastore stuff
from db.common_functions import *

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
	
@application.route("/admin/", methods=["GET", "POST"])
@login_required
def admPage():
    return render_template("admin.html", prideMonth=True, visits=get_last_visits())
	

@application.route("/testquery")
def testquery():
	#create_solo_membership(1, "", "", "")
	##get_last_visits()
	create_fake_users()
	return "no"
