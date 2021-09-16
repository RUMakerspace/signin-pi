from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./datastore_local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    rums_pk = db.Column(db.Integer, primary_key=True)
    netid = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)


# We store card number as a string due to the undetermined length of it.  Convert to int and back to string for all operations.
class Card(db.Model):
    card_pk = db.Column(db.Integer, primary_key=True)
    rums_pk = db.Column(db.Integer, db.ForeignKey("user.rums_pk"), nullable=False)
    card_no = db.Column(db.String(20), unique=True, nullable=False)
    zk_pk = db.Column(db.Integer, nullable=True, unique=True)

    # The ZK_PK is stored here instead of in the user model due to the overlap in how ZK stores cards; as people.

    def __repr__(self):
        return "<Card %r>" % self.card_no


# This allows us to have global site and visit tracking unique to a given site and stuff. That way Ag stuff doesn't interfere with Livi, etc.
class Site(db.Model):
    site_pk = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(20), nullable=False)
    short_name = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return "<Site %r>" % self.site_name


class SoloMembership(db.Model):
    membership_pk = db.Column(db.Integer, primary_key=True)
    rums_pk = db.Column(
        db.Integer, db.ForeignKey("user.rums_pk"), nullable=True
    )  # we can template and set them up without a user but it's heavily discouraged.
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    human_name = db.Column(
        db.String(20), nullable=False
    )  # Not nullable, must have some name for users even if just "Solo Membership."

    def __repr__(self):
        return """<SoloMembership {} {}>""".format(self.membership_pk, self.human_name)


class GroupMembership(db.Model):
    membership_pk = db.Column(db.Integer, primary_key=True)
    human_name = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    admin_user = db.Column(db.Integer, db.ForeignKey("user.rums_pk"), nullable=True)

    def __repr__(self):
        return """<GroupMembership {} {}>""".format(self.membership_pk, self.human_name)


class GroupMember(db.Model):
    membership_pk = db.Column(db.Integer, primary_key=True)
    group_membership_pk = db.Column(
        db.ForeignKey("groupmembership.membership_pk"), nullable=False
    )
    rums_pk = db.Column(db.Integer, db.ForeignKey("user.rums_pk"), nullable=False)

    def __repr__(self):
        return """<GroupMember {}>""".format(self.membership_pk)
