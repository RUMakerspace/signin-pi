from flask import (
    Blueprint,
    render_template,
    abort,
    request,
    flash,
    redirect,
    url_for,
    make_response,
    jsonify,
)

import shelve

from jinja2 import TemplateNotFound
from flask_login import LoginManager, login_required
from model.datastore import *  # so we can query using internal models.
from datetime import date, datetime, timedelta  # used for broken shit.
from dateutil import tz
from helpers.timezone import convertTZ, todayInEST  # used to render in EST.

staff_signin = Blueprint("staff_signin", __name__, template_folder="templates")

shelvestore = shelve.open("db/staff_signin.shelve.db", writeback=True)

# main route of admin page.
@staff_signin.route("/", methods=["GET", "POST"])
def mainRoute():
    if request.method == "GET":
        return render_template("staff_signin.html")
    if request.method == "POST":
        cookies = request.cookies.to_dict()

        print(request.form.to_dict())
        currentSite = Site.query.filter(Site.site_pk == cookies["campus"]).first()
        currentCard = Card.query.filter(
            Card.card_no == request.form.to_dict()["cardNo"]
        ).first()
        currentUser = None

        if currentCard.rums_pk != None:
            currentUser = User.query.filter(User.rums_pk == currentCard.rums_pk).first()

        if currentUser == None:
            flash("Make a normal profile first please!")
            return redirect(url_for("indexPage"))

        if "stafflogs" not in shelvestore:
            shelvestore["stafflogs"] = []

        # verify that there actually are visits they're not signed in for to sign them out.
        tempVisitsStaff = [
            x
            for x in shelvestore["stafflogs"]
            if x["exit"] == None and x["rums_pk"] == currentUser.rums_pk
        ]
        if len(tempVisitsStaff) > 0:
            tempVisitsStaff[0]["exit"] = datetime.now(timezone.utc)
            flash("signed out, thank you.")
        else:
            shelvestore["stafflogs"].append(
                {
                    "exit": None,
                    "rums_pk": currentUser.rums_pk,
                    "entry": datetime.now(timezone.utc),
                    "name": currentUser.name,
                }
            )
            flash("Signed in, thank you ".format(currentUser.name))
        shelvestore.sync()
        return redirect(url_for("indexPage"))


@staff_signin.route("/viewstafflogs")
def staffLogs():
    return jsonify(shelvestore["stafflogs"])
