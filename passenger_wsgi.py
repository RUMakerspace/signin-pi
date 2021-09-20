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
from helpers.membership import allowEntry
from helpers.membership import getAllMemberships


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


from model.datastore import (
    Site,
    Card,
    User,
    Visit,
    SoloMembership,
    GroupMembership,
    GroupMember,
)


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


@application.route("/entryGranter")
def t1(message=None):

    cookies = request.cookies.to_dict()

    currentSite = Site.query.filter(Site.site_pk == cookies["campus"]).first()
    currentCard = Card.query.filter(Card.card_no == cookies["cardNo"]).first()
    currentUser = None

    if currentCard.rums_pk != None:
        currentUser = User.query.filter(User.rums_pk == currentCard.rums_pk).first()

    currentUserVisits = Visit.query.filter(
        Visit.rums_pk == currentUser.rums_pk
    ).order_by(Visit.entry_time.desc())

    numVisits = currentUserVisits.count()
    lastVisitDate = currentUserVisits.first().entry_time.strftime("%Y/%m/%d")

    print("current user")
    print(currentUser)
    print(cookies)

    memberships = getAllMemberships(currentUser.rums_pk)
    pageData = {}
    # pageData should contain their name, their NetID, their 'division', and their membership types.
    return render_template(
        "signedIn.html",
        prideMonth=True,
        site=currentSite,
        card=currentCard,
        user=currentUser,
        numVisits=numVisits,
        lastVisitDate=lastVisitDate,
        memberships=memberships,
    )


@application.route("/denied")
def deniedAccess():
    return render_template(
        "access_denied.html", prideMonth=True, deniedType="cardNotFound"
    )


@application.route("/api/checkSignin", methods=["POST"])
def userHasEntry():

    # The response is to set the appropriate cookies for
    # passing it back, so that we can safely check on
    # the next page without recycling them.

    apiResponse = make_response(redirect(url_for("t1")))

    # get us the site pk
    campus = None
    if "campus" in request.cookies.to_dict():
        campus = int(request.cookies.to_dict()["campus"])

    currentSite = Site.query.filter_by(site_pk=campus).first()

    # Forcibly converting to/from gets us
    cardNo = str(int(str((request.form.to_dict())["cardNo"])))
    apiResponse.set_cookie("cardNo", cardNo)

    matchCards = Card.query.filter_by(card_no=cardNo)

    # If the card does not exist in the database, add it.
    if matchCards.count() == 0:
        tempCard = Card(card_no=cardNo)
        db.session.add(tempCard)
        db.session.commit()
        print("added card {}".format(cardNo))
        # Reload our reference in case the above changed it.
        matchCards = Card.query.filter_by(card_no=cardNo)

    if matchCards.count() != 0:
        print(list(matchCards))

    if currentSite.allow_entry_without_profile:
        return t1(
            "We've collected your card number for now; we can re-associate it with your profile at a later date."
        )  # if the user can enter as-is we collect their card number and say granted.  Otherwise we fill it out.

    return apiResponse


@application.route("/api/setCampus/<campusShort>", methods=["GET"])
def apiSetCampus(campusShort):

    xg = make_response(redirect(url_for("indexPage")))

    campusID = (Site.query.filter_by(short_name=campusShort)).first().site_pk

    xg.set_cookie("campus", str(campusID), max_age=60 * 60 * 24 * 365 * 2)  # 2 years.

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

    campuses = Site.query.all()
    visits = Visit.query.join(User, Visit.rums_pk == User.rums_pk).limit(20).all()

    solomemberships = SoloMembership.query.limit(20).all()
    groupmem = (
        GroupMember.query.join(
            GroupMembership,
            GroupMember.group_membership_pk == GroupMembership.membership_pk,
        )
        .limit(20)
        .all()
    )

    return render_template(
        "admin.html",
        prideMonth=True,
        campuses=campuses,
        visits=visits,
        group_memberships=groupmem,
        solo_memberships=solomemberships,
    )


@application.route("/testquery")
def testquery():

    currentSite = Site.query.filter_by(site_pk=1).first()
    currentUser = User.query.filter_by(rums_pk=1).first()
    currentGroupMembership = GroupMembership.query.get(1)

    # th = Visit(rums_pk=1, card_pk=1, site_pk=1, entry_time=datetime.utcnow(), granted=1)
    # db.session.add(th)
    # db.session.commit()

    # gq = GroupMembership(site_pk=currentSite.site_pk, admin_user = currentUser.rums_pk, human_name="Test Group Membership", start_date = datetime.utcnow())

    # gq = GroupMember(rums_pk=currentUser.rums_pk, group_membership_pk = currentGroupMembership.membership_pk)
    # db.session.add(gq)
    # db.session.commit()

    # if allowEntry(1, 1):
    #    return "yer in bitch"

    return "no"
