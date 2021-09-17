from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    rums_pk = db.Column(db.Integer, primary_key=True)
    netid = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    picture = db.Column(db.LargeBinary, nullable=True)

    def __repr__(self):
        return "<User {} {}>".format(rums_pk, email)


class Visit(db.Model):
    visit_pk = db.Column(db.Integer, primary_key=True)
    rums_pk = db.Column(db.Integer, db.ForeignKey("user.rums_pk"), nullable=True)
    card_pk = db.Column(db.String(20), db.ForeignKey("card.card_pk"), nullable=False)
    entry_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    exit_time = db.Column(
        db.DateTime, nullable=True, default=None
    )  # Must always update on exit or close for the day.
    granted = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return "<Visit {} {} {} {}>".format(visit_pk, card_no, entry_time, granted)


# This allows us to have global site and visit tracking unique to a given site and stuff. That way Ag stuff doesn't interfere with Livi, etc.
class Site(db.Model):
    site_pk = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(20), nullable=False)
    short_name = db.Column(db.String(20), nullable=False)
    allow_entry_without_profile = db.Column(db.Boolean, nullable=False, default=False)
    rutgers_active_only = db.Column(db.Boolean, nullable=False, default=False)
    # Allow_entry_w.o_profile is used to track site-specific sign-in where their visit
    # is recorded without a person ID so it can later be associated with a rums_pk.

    # This is useful to allow things like RUMakers visits without a complete profile.

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
        db.ForeignKey("group_membership.membership_pk"), nullable=False
    )
    rums_pk = db.Column(db.Integer, db.ForeignKey("user.rums_pk"), nullable=False)

    def __repr__(self):
        return """<GroupMember {}>""".format(self.membership_pk)
