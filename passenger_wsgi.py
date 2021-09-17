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


datastore = SQLAlchemy(application)

users = Users("./db/users.json", application)


class User(datastore.Model):
    rums_pk = datastore.Column(datastore.Integer, primary_key=True)
    netid = datastore.Column(datastore.String(20), unique=True, nullable=True)
    email = datastore.Column(datastore.String(50), nullable=False)
    name = datastore.Column(datastore.String(100), nullable=False)


# We store card number as a string due to the undetermined length of it.  Convert to int and back to string for all operations.
class Card(datastore.Model):
    card_pk = datastore.Column(datastore.Integer, primary_key=True)
    rums_pk = datastore.Column(
        datastore.Integer, datastore.ForeignKey("user.rums_pk"), nullable=True
    )
    card_no = datastore.Column(datastore.String(20), unique=True, nullable=False)
    zk_pk = datastore.Column(datastore.Integer, nullable=True, unique=True)

    # The ZK_PK is stored here instead of in the user model due to the overlap in how ZK stores cards; as people.

    def __repr__(self):
        return "<Card %r>" % self.card_no


"""INSERT INTO visits (rums_pk, card_no, entry_time, exit_time, granted) VALUES ({}, "{}", datetime('now'), {} 1)"""


class Visit(datastore.Model):
    visit_pk = datastore.Column(datastore.Integer, primary_key=True)
    rums_pk = datastore.Column(
        datastore.Integer, datastore.ForeignKey("user.rums_pk"), nullable=True
    )
    card_pk = datastore.Column(
        datastore.String(20), datastore.ForeignKey("card.card_pk"), nullable=False
    )
    entry_time = datastore.Column(
        datastore.DateTime, nullable=False, default=datetime.utcnow
    )
    exit_time = datastore.Column(
        datastore.DateTime, nullable=True, default=None
    )  # Must always update on exit or close for the day.
    granted = datastore.Column(datastore.Boolean, nullable=False)

    def __repr__(self):
        return "<Visit {} {} {} {}>".format(visit_pk, card_no, entry_time, granted)


# This allows us to have global site and visit tracking unique to a given site and stuff. That way Ag stuff doesn't interfere with Livi, etc.
class Site(datastore.Model):
    site_pk = datastore.Column(datastore.Integer, primary_key=True)
    site_name = datastore.Column(datastore.String(20), nullable=False)
    short_name = datastore.Column(datastore.String(20), nullable=False)
    allow_entry_without_profile = datastore.Column(
        datastore.Boolean, nullable=False, default=False
    )
    # Allow_entry_w.o_profile is used to track site-specific sign-in where their visit
    # is recorded without a person ID so it can later be associated with a rums_pk.

    # This is useful to allow things like RUMakers visits without a complete profile.

    def __repr__(self):
        return "<Site %r>" % self.site_name


class SoloMembership(datastore.Model):
    membership_pk = datastore.Column(datastore.Integer, primary_key=True)
    rums_pk = datastore.Column(
        datastore.Integer, datastore.ForeignKey("user.rums_pk"), nullable=True
    )  # we can template and set them up without a user but it's heavily discouraged.
    start_date = datastore.Column(
        datastore.DateTime, nullable=False, default=datetime.utcnow
    )
    end_date = datastore.Column(datastore.DateTime, nullable=True)
    human_name = datastore.Column(
        datastore.String(20), nullable=False
    )  # Not nullable, must have some name for users even if just "Solo Membership."

    def __repr__(self):
        return """<SoloMembership {} {}>""".format(self.membership_pk, self.human_name)


class GroupMembership(datastore.Model):
    membership_pk = datastore.Column(datastore.Integer, primary_key=True)
    human_name = datastore.Column(datastore.String(20), nullable=False)
    start_date = datastore.Column(
        datastore.DateTime, nullable=False, default=datetime.utcnow
    )
    end_date = datastore.Column(datastore.DateTime, nullable=True)
    admin_user = datastore.Column(
        datastore.Integer, datastore.ForeignKey("user.rums_pk"), nullable=True
    )

    def __repr__(self):
        return """<GroupMembership {} {}>""".format(self.membership_pk, self.human_name)


class GroupMember(datastore.Model):
    membership_pk = datastore.Column(datastore.Integer, primary_key=True)
    group_membership_pk = datastore.Column(
        datastore.ForeignKey("group_membership.membership_pk"), nullable=False
    )
    rums_pk = datastore.Column(
        datastore.Integer, datastore.ForeignKey("user.rums_pk"), nullable=False
    )

    def __repr__(self):
        return """<GroupMember {}>""".format(self.membership_pk)


datastore.create_all()
# This is used to ensure all tables exist.


# Datastore stuff
from db.common_functions import *
from db.sqlite_store import setupTables


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
