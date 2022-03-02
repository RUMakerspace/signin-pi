from helpers.timezone import convertTZ, todayInEST
from model.datastore import *
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
from flask_login import LoginManager, login_required

reports = Blueprint("reports", __name__, template_folder="templates")


@reports.route("/")
@login_required
def mainVisitsReportPage():
    return render_template("all_reports.html")


@reports.route("/visitsByDay")
@login_required
def reportPage():
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
        .all()
    )

    visitDays = []
    for v in visits:
        if convertTZ(v.entry_time).strftime("%Y-%m-%d") not in visitDays:
            visitDays.append(convertTZ(v.entry_time).strftime("%Y-%m-%d"))

    # return str(visitDays)

    for k, vd in enumerate(visitDays):
        g = len(
            [x for x in visits if convertTZ(x.entry_time).strftime("%Y-%m-%d") == vd]
        )
        visitDays[k] = [vd, g]
    # convertTZ(visit.entry_time).strftime("%a %b %d, %Y at %I:%M %p")

    visitDays = sorted(visitDays, key=lambda x: x[0])

    # pprint(visits)

    return render_template("report.html", visitDays=visitDays)


@reports.route("/visits")
@login_required
def visitsReportPage():
    numPerPage = 50
    if not request.args.get("pageNo"):
        page = 0
    else:
        page = int(request.args.get("pageNo"))

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
        .offset(numPerPage * page)
        .limit(numPerPage)
        .all()
    )

    return render_template(
        "visits_page.html",
        prideMonth=True,
        visits=visits,
        numPerPage=numPerPage,
        pageNo=page,
        convertTZ=convertTZ,  # helper method to localize UTC timestamps.
    )


@reports.route("/userNetIDs")
@login_required
def netIDUsernamesReports():
    users = User.query.filter(User.shadow_profile == 0).all()

    return render_template(
        "netID_report.html",
        users=users,
    )
