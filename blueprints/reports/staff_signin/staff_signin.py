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
from helpers.visit import signOutAllUsers
from datetime import date, datetime, timedelta  # used for broken shit.
from dateutil import tz

from helpers.timezone import convertTZ, todayInEST  # used to render in EST.
import base64  # used for profile pic functions.


staff_signin = Blueprint("staff", __name__, template_folder="templates")

# main route of admin page.
@admin.route("/", methods=["GET", "POST"])
