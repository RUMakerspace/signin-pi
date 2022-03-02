from flask import (
    Blueprint,
    render_template,
    abort,
    request,
    flash,
    redirect,
    url_for,
    make_response,
)
from jinja2 import TemplateNotFound
from flask_login import LoginManager, login_required
from model.datastore import *  # so we can query using internal models.

from datetime import date, datetime, timedelta  # used for broken shit.
from dateutil import tz

from helpers.timezone import convertTZ, todayInEST, todayEST2  # used to render in EST.
import base64  # used for profile pic functions.


admin = Blueprint("admin", __name__, template_folder="templates")

# main route of admin page.
@admin.route("/", methods=["GET", "POST"])
@login_required
def admPage():
    print(request.cookies.to_dict())

    campuses = Site.query.all()
    visits = (
        Visit.query.join(User, Visit.rums_pk == User.rums_pk)
        .join(Site, Visit.site_pk == Site.site_pk)
        .add_columns(
            User.name,
            User.rums_pk,
            User.pronouns,
            User.netid,
            User.email,
            Visit.exit_time,
            Visit.entry_time,
            Visit.granted,
            Visit.visit_pk,
            Site.short_name,
        )
        .order_by(Visit.entry_time.desc())
        .limit(20)
        .all()
    )

    # Timezone filtering broken atm, fix!
    # https://stackoverflow.com/questions/14972802/determine-start-and-end-time-of-current-day-utc-est-utc-python
    start = todayEST2()  # helper, may not work?
    end = start + timedelta(1)

    print(start)
    print(end)

    totalVisits = len(Visit.query.all())
    todayVisits = len(Visit.query.filter((Visit.entry_time > start)).all())

    print(todayVisits)

    solomemberships = SoloMembership.query.limit(20).all()
    groupmem = (
        GroupMember.query.join(
            GroupMembership,
            GroupMember.group_membership_pk == GroupMembership.membership_pk,
        )
        .limit(20)
        .all()
    )

    users = User.query.filter(User.shadow_profile == 0).all()

    return render_template(
        "admin_main.html",
        prideMonth=True,
        campuses=campuses,
        visits=visits,
        group_memberships=groupmem,
        solo_memberships=solomemberships,
        users=users,
        convertTZ=convertTZ,  # helper method to localize UTC timestamps.
        totalVisits=totalVisits,
        todayVisits=todayVisits,
    )


# Edit user page.
@admin.route("/editUser", methods=["GET", "POST"])
@login_required
def editUser():
    if request.method == "POST":
        newData = request.form.to_dict()
        print(newData)
        print(request.args.to_dict())
        print(request.files.to_dict())

        rums_pk = request.args.to_dict()["user_pk"]
        currentUser = User.query.filter(User.rums_pk == rums_pk).first()

        currentUser.email = newData["inputRUEmail"]
        currentUser.name = newData["inputName"]
        currentUser.pronouns = newData["inputPronouns"]
        currentUser.netid = newData["inputNetID"]

        if "profilePic" in request.files:
            print("User submitted new profile pic, checking.")
            fileHolder = request.files["profilePic"].read()
            if (len(fileHolder)) > 0:
                print("User profile pic is not empty")
                currentUser.picture = base64.b64encode(fileHolder)

        currentUser.rutgersActive = False
        if "rutgersActive" in newData:
            currentUser.rutgers_active = True

        currentUser.rutgersVerified = False
        if "rutgersVerified" in newData:
            currentUser.rutgers_verified = True

        db.session.commit()
        flash("User successfully edited.")

    if "user_pk" not in request.args.to_dict():
        return redirect(url_for("error", loadTimer=5000))
    else:
        user_pk = request.args.to_dict()["user_pk"]

    whichUser = User.query.filter(User.rums_pk == user_pk).first()
    visits = Visit.query.filter(Visit.rums_pk == user_pk).all()
    cards = Card.query.filter(Card.rums_pk == user_pk).all()

    print(whichUser.shadow_profile)

    return render_template(
        "edit_user.html",
        user=whichUser,
        visits=visits,
        cards=cards,
        convertTZ=convertTZ,
    )


# API core routes.
@admin.route("api/setCampus/<campusShort>", methods=["GET"])
@login_required
def apiSetCampus(campusShort):

    xg = make_response(redirect(url_for("indexPage")))

    campusID = (Site.query.filter_by(short_name=campusShort)).first().site_pk

    xg.set_cookie("campus", str(campusID), max_age=60 * 60 * 24 * 365 * 2)  # 2 years.

    print(request.cookies.to_dict())
    return xg


# API function to remove card from a user.
@admin.route("api/removeCardFromExistence/<cardNo>")
@login_required
def removeCardFuckYou(cardNo):
    tempCard = Card.query.filter(Card.card_no == cardNo)
    print(tempCard)
    tempCard.delete()
    db.session.commit()
    flash("Card removed from user.")
    return redirect(url_for("admin.admPage"))


# delete accidental visits.
@admin.route("api/delVisit/<visit_pk>")
@login_required
def delVisit(visit_pk):
    visitTemp = Visit.query.filter(Visit.visit_pk == visit_pk).first()

    db.session.delete(visitTemp)
    db.session.commit()

    print("Deleted visit {}".format(visit_pk))

    return redirect(url_for("admin.admPage"))


# sign out user instantaneously.
@admin.route("api/makeSignout/<visit_pk>")
@login_required
def signuserOutVisit(visit_pk):
    visitTemp = Visit.query.filter(Visit.visit_pk == visit_pk).first()

    visitTemp.exit_time = datetime.utcnow()
    db.session.commit()

    return redirect(url_for("admin.admPage"))


@admin.route("api/removeFalseSignout/<visit_pk>")
@login_required
def visitRemoveFalseSignout(visit_pk):
    visitTemp = Visit.query.filter(Visit.visit_pk == visit_pk).first()

    visitTemp.exit_time = None
    db.session.commit()

    return redirect(url_for("admin.admPage"))


@admin.route("api/signOutCampusUsers/<site>")
@login_required
def signOutCampusUsers(site):

    signOutAllUsers(site)

    return redirect(url_for("admin.admPage"))
