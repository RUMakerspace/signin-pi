import sys, os
import json
import datetime
import re
from pprint import pprint

# Flask
import sqlite3
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    make_response,
    flash,
)
import flask

# Flask SQLAlchemy shit.
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler  # for midnight job rollover shit.

from datetime import datetime, timedelta

# Flask Login
from model.users import Users
import flask_login
from flask_login import LoginManager, login_required, login_user, logout_user

application = Flask(__name__)
application.secret_key = open("supersecret.key").read()


scheduler = APScheduler()
scheduler.api_enabled = True  # may need to be disabled
scheduler.init_app(application)
application.app_context().push()
scheduler.start()

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

from blueprints.admin.admin import admin
from blueprints.reports.reports import reports
from blueprints.staff_signin.staff_signin import staff_signin

application.register_blueprint(admin, url_prefix="/admin")
application.register_blueprint(reports, url_prefix="/reports")
application.register_blueprint(staff_signin, url_prefix="/staff")

from helpers.visit import signOutAllUsers


@scheduler.task(
    "cron", id="sign_off_forgotten_students", minute=0, hour=4, day="*", month="*"
)
def signOffForgottenMidnight():
    # signOutCampusUsers

    with application.app_context():

        sites = Site.query.all()

        for s in sites:
            signOutAllUsers(s.site_pk)
            print("Signed users out of {}".format(s.site_name))
        print("Signed off students who forgot to sign out.")


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


@application.errorhandler(500)
def pageNotFound(error):
    return redirect(url_for("error", loadTimer=5000))


### LOGIN MANAGER
login_manager = flask_login.LoginManager()
login_manager.init_app(application)

# Does this work?
login_manager.blueprint_login_views = {"admin": "login"}

# This function is just to set a session timer.
@application.before_request
def before_request():
    # flask.session.permanent = True
    # application.permanent_session_lifetime = timedelta(minutes=20)
    # flask.session.modified = True
    pass


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
    loadTimer = 0
    if "loadTimer" in request.args.to_dict():
        loadTimer = 5000

    campusID = int(request.cookies.to_dict()["campus"])

    if "campus" not in request.cookies.to_dict():
        return "Campus not set, log in to admin page to set please."

    print("Campus ID\t{}".format(campusID))

    campusName = Site.query.filter_by(site_pk=campusID).first().site_name

    xg = make_response(
        render_template(
            "visitor_signin.html",
            siteName=campusName,
            prideMonth=True,
            loadTimer=loadTimer,
        )
    )

    return xg


@application.route("/simpleGrantedPage")
def simpleGranted():
    return render_template("signedIn.html")


@application.route("/entryGranter")
def mainEntryGranter(message=None):

    if "loadTimer" in (request.args.to_dict()):
        loadTimer = request.args.to_dict()["loadTimer"]
    else:
        loadTimer = None

    cookies = request.cookies.to_dict()

    currentSite = Site.query.filter(Site.site_pk == cookies["campus"]).first()
    currentCard = Card.query.filter(
        Card.card_no == request.args.to_dict()["cardNo"]
    ).first()
    currentUser = None

    if currentCard.rums_pk != None:
        currentUser = User.query.filter(User.rums_pk == currentCard.rums_pk).first()

    currentUserVisits = Visit.query.filter(
        Visit.rums_pk == currentUser.rums_pk
    ).order_by(Visit.entry_time.desc())

    numVisits = currentUserVisits.count()
    lastVisitDate = currentUserVisits.first()

    if lastVisitDate != None:
        lastVisitDate = lastVisitDate.entry_time.strftime("%Y/%m/%d")

    # print("current user")
    print(currentUser)
    # print(cookies)

    memberships = getAllMemberships(currentUser.rums_pk)

    return render_template(
        "signedIn.html",
        prideMonth=True,
        site=currentSite,
        card=currentCard,
        user=currentUser,
        numVisits=numVisits,
        lastVisitDate=lastVisitDate,
        memberships=memberships,
        loadTimer=loadTimer,
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
from helpers.user import setupUserExists
from helpers.visit import createVisit, userIsAtSite, signUserOut
from helpers.membership import hasValidMembership


@application.route("/error")
def error():
    return render_template("error.html")


@application.route("/signedOut")
def signedOut():
    return render_template("signedOut.html")


@application.route("/api/checkSignin", methods=["POST", "GET"])
def userHasEntry():

    # The response is to set the appropriate cookies for
    # passing it back, so that we can safely check on
    # the next page without recycling them.

    # get us the site pk
    campus = None
    if "campus" in request.cookies.to_dict():
        campus = int(request.cookies.to_dict()["campus"])

    currentSite = Site.query.filter_by(site_pk=campus).first()

    # Forcibly converting to/from gets us
    if "cardNo" in request.form.to_dict():
        cardNo = str(int(str((request.form.to_dict())["cardNo"])))

    if "cardNo" in request.args.to_dict():
        cardNo = str(int(str((request.args.to_dict())["cardNo"])))

    apiResponse = make_response(
        redirect(url_for("mainEntryGranter", loadTimer=5000, cardNo=cardNo))
    )

    userTemp = userExists(cardNo)  # user exists returns the user or a new one.

    print(userTemp)

    if userIsAtSite(userTemp.rums_pk, currentSite.site_pk):
        print("User is currently signed in at the current site, signing out!")
        signUserOut(userTemp.rums_pk, currentSite.site_pk)
        return render_template("signedout.html", prideMonth=True, loadTimer=5000)

    if currentSite.allow_entry_without_profile:
        print("user is allowed entry without profile.")
        # be sure to write
        return redirect(url_for("mainEntryGranter", no_profile=True, loadTimer=5000))
    # This is the simple access granted page that collects card / shadow profile otherwise and lets them in automatically.

    else:
        print(
            "User is not allowed entry without profile, must sign in or be verified normally."
        )

        if userTemp.shadow_profile:  # shadow profile catchall.
            print("User currently has shadow profile, gotta deal with that.")
            tempRedir = make_response(
                redirect(url_for("firstVisit", cardNo=cardNo))
            )  # five minute expiry for other users typing shit in.
            return tempRedir

        else:  # not a ahadow profile, normal auth flow.
            print("User has a real profile, check full auth flow shit.")
            if userTemp.rutgers_active:
                print("User is active Rutgers, allowing entry.")
                createVisit(userTemp.rums_pk, cardNo, currentSite.site_pk, 1)
                return apiResponse

            if not userTemp.rutgers_active:
                print("User is not active Rutgers, checking other rules.")
                if currentSite.rutgers_active_only:
                    print("Current site is Rutgers active only, denying entry.")
                    createVisit(userTemp.rums_pk, cardNo, currentSite.site_pk, 0)
                    return render_template(
                        "access_denied.html", deniedType="nonRutgers", loadTimer=5000
                    )
                if not currentSite.rutgers_active_only:
                    print("Site is open to non-Rutgers active with membership!")
                    hasValidMem = hasValidMembership(userTemp, currentSite)
                    if hasValidMem:  # they can enter.
                        print("Has a presently valid membership, granting access.")
                        createVisit(userTemp.rums_pk, cardNo, currentSite.site_pk, 1)
                        return apiResponse
                    else:
                        print("No valid membership, denied, expired.")
                        createVisit(userTemp.rums_pk, cardNo, currentSite.site_pk, 0)
                        return render_template(
                            "access_denied.html", deniedType="expired", loadTimer=5000
                        )

            # check normal rutgers decision flow.
    print("We should not be here.")

    return redirect(url_for("deniedAccess"))


@application.route("/firstvisit", methods=["GET", "POST"])
def firstVisit():
    if request.method == "POST":
        data = request.form.to_dict()

        print(data)

        try:
            cardNo = data["cardNo"]
        except:
            redirect(url_for("error", loadTimer=5000))

        tempCard = Card.query.filter(Card.card_no == cardNo).first()
        tempUser = User.query.filter(User.rums_pk == tempCard.rums_pk).first()
        # TODO use setupUserExists and migrate most of this to helper functions.

        qg = setupUserExists(email=data["inputRUEmail"], netid=data["inputNetID"])
        if qg != None:
            print("User exists with email and name, assigning card to them.")
            tempCard.rums_pk = qg.rums_pk

            db.session.commit()

        else:
            print("No user exists with current email or netID, new profile made.")
            tempUser.email = data["inputRUEmail"]
            tempUser.netid = data["inputNetID"]
            tempUser.name = data["inputName"]

            if "inputOtherPronouns" in data:
                tempUser.pronouns = data["inputOtherPronouns"]

            tempUser.rutgers_active = 1
            tempUser.shadow_profile = 0  # This is so they don't have to do it again.

            # TODO:
            # If user has NetID, set rutgers active against Rutgers NetID, if they selected last items don't.
            # Also TODO add visit.
            db.session.commit()

        return redirect(url_for("userHasEntry", cardNo=tempCard.card_no))

    else:
        return render_template(
            "firstvisit.html",
            cardNo=request.args.to_dict()["cardNo"],
            loadTimer=(1000 * 5 * 60),
        )

    # return render_template("firstvisit.html", prideMonth=True)
