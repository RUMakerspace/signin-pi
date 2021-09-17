import sys, os
import json
import datetime
import re
from pprint import pprint

# Print Databases
from queue import Queue

# Flask
import sqlite3
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    make_response,
)
import flask

# Flask SQLAlchemy shit.
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# Flask Login
from model.users import Users
import flask_login
from flask_login import LoginManager, login_required, login_user, logout_user

application = Flask(__name__)
application.secret_key = open("supersecret.key").read()

application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./db/datastore_local.db"
# We may change this to another app at some point, like MariaDB but for now, this is fine.

application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


users = Users("./db/users.json", application)

# This is used to ensure all tables exist.

from model.datastore import db

application.app_context().push()
db.init_app(application)
db.create_all()

# Datastore stuff


### LOGIN MANAGER
login_manager = flask_login.LoginManager()
login_manager.init_app(application)

# This function is just to set a session timer.
@application.before_request
def before_request():
    flask.session.permanent = True
    application.permanent_session_lifetime = timedelta(minutes=20)
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


from model.datastore import Site


@application.route("/")
def indexPage():
    campusID = int(request.cookies.to_dict()["campus"])

    print("Campus ID\t{}".format(campusID))

    campusName = Site.query.filter_by(site_pk=campusID).first().site_name

    xg = make_response(
        render_template("visitor_signin.html", siteName=campusName, prideMonth=True)
    )
    if "campus" not in request.cookies.to_dict():
        return "Campus not set, log in to admin page to set please."
    return xg


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
    campus = None
    if "campus" in request.cookies.to_dict():
        campus = requests.cookies.to_dict()["campus"]

    return redirect(url_for("t1"))


@application.route("/api/setCampus/<campusShort>", methods=["GET"])
def apiSetCampus(campusShort):

    xg = make_response(redirect(url_for("indexPage")))
    # if "campus" not in request.cookies.to_dict():

    print(campusShort)

    campusID = (Site.query.filter_by(short_name=campusShort)).first().site_pk

    print(int(str(campusID)))

    xg.set_cookie("campus", str(campusID), max_age=60 * 60 * 24 * 365 * 2)  # 2 years.
    # return "Campus not set, log in to admin page to set please."
    print(request.cookies.to_dict())
    return xg


@application.route("/firstvisit", methods=["GET", "POST"])
def firstVisit():
    if request.method == "POST":
        print(request.form.to_dict())

    return render_template("firstvisit.html", prideMonth=True)


@application.route("/admin/", methods=["GET", "POST"])
@login_required
def admPage():
    print(request.cookies.to_dict())
    return render_template("admin.html", prideMonth=True, campuses=Site.query.all())


@application.route("/testquery")
def testquery():
    testCard = Card(card_no="1257125712571923")
    datastore.session.add(testCard)
    datastore.session.commit()

    return "no"
