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


# This sets up our ability to query the database in this class, and also creates the
# database tables we need to represent our membership objects, sites, etc.
application.app_context().push()
db.init_app(application)
db.create_all()

from model.datastore import (
    Site,
    Card,
    User,
    Visit,
    SoloMembership,
    GroupMembership,
    GroupMember,
)

# This config is simply used to represent our initial site configuration
# for repeatedly creating new simulated setups for mocking ig?
import json

config_sites = json.loads(open("./db/sites.json", "r").read())
# Datastore stuff

# This builds the default sites from the config file to avoid errors
# on the front-page.  Additional sites may be added temporarily.

for site in config_sites:
    try:
        tempSite = Site(
            site_name=site["full_name"],
            short_name=site["short"],
            rutgers_active_only=site["rutgers_only"],
            allow_entry_without_profile=0,
        )
        db.session.add(tempSite)
        db.session.commit()
    except:
        pass

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

    if "campus" not in request.cookies.to_dict():
        return "Campus not set, log in to admin page to set please."

    print("Campus ID\t{}".format(campusID))

    campusName = Site.query.filter_by(site_pk=campusID).first().site_name

    xg = make_response(
        render_template("visitor_signin.html", siteName=campusName, prideMonth=True)
    )

    return xg


@application.route("/simpleGrantedPage")
def simpleGranted():
    return render_template("signedIn.html")


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
    lastVisitDate = currentUserVisits.one_or_none()

    if lastVisitDate != None:
        lastVisitDate = lastVisitDate.entry_time.strftime("%Y/%m/%d")

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

    # cardNotFound, expired
    return render_template(
        "access_denied.html", prideMonth=True, deniedType="cardNotFound"
    )


# we need to change it such that the card model must have a rums_pk
# but the rums_pk can have nothing except itself.
# This allows us to have "shadow profiles" until it's time to set
# them up and guarantees we can maintain the one-to-many of users to
# cards.

from helpers.user import createShadowUserByCardNo, userExists


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

    userTemp = userExists(cardNo)  # user exists returns the user or False only.

    # If the profile does not exist we make them one to keep track of them no matter what.
    if userTemp == None:
        userTemp = createShadowUserByCardNo(cardNo)

    print(userTemp)

    if currentSite.allow_entry_without_profile:
        print("user is allowed entry without profile.")
        # be sure to write
        return render_template(
            "signedIn.html", no_profile=True
        )  # This is the simple access granted page that collects card / shadow profile otherwise and lets them in automatically.

    else:
        print(
            "User is not allowed entry without profile, must sign in or be verified normally."
        )
        if userTemp.shadow_profile:
            print("User currently has shadow profile, gotta deal with that.")
            return redirect(url_for("firstVisit"))
        else:
            print("User has a real profile, check full auth flow shit.")
            return ""
            # check normal rutgers decision flow.
    print("We should not be here.")

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
        data = request.form.to_dict()
        cookies = request.cookies.to_dict()

        print(cookies)

        tempUser = userExists(cookies["cardNo"])

        tempUser.email = data["inputRUEmail"]
        tempUser.netid = data["inputNetID"]
        tempUser.name = data["inputName"]
        tempUser.rutgers_active = 1
        tempUser.shadow_profile = 0  # This is so they don't have to do it again.

        # TODO:
        # If user has NetID, set rutgers active against Rutgers NetID, if they selected last items don't.
        # Also TODO add visit.
        db.session.commit()

        return redirect(url_for("t1"))

    else:
        return render_template("firstvisit.html", prideMonth=True)

    # return render_template("firstvisit.html", prideMonth=True)


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

    # createShadowUserByCardNo(2188119300)

    # if allowEntry(1, 1):
    #    return "yer in bitch"

    return "no"
