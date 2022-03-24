from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

# Site
# User
# Card
# Visit

# SoloMembership
# GroupMembership
# GroupMember

class Card(db.Model):
    card_pk = db.Column(db.Integer, primary_key=True)
    card_no = db.Column(db.String(20), unique=True, nullable=False)
    zk_pk = db.Column(db.Integer, nullable=True)
    rums_pk = db.Column(db.Integer, db.ForeignKey("user.rums_pk"), nullable=False)

    def __repr__(self):
        return "<Card {} {}>".format(self.card_pk, self.card_no)


class User(db.Model):
    rums_pk = db.Column(db.Integer, primary_key=True)
    netid = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(50), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    picture = db.Column(db.LargeBinary, nullable=True)
    pronouns = db.Column(db.String(20), nullable=True)
    rutgers_active = db.Column(db.Boolean, nullable=True)
    shadow_profile = db.Column(db.Boolean, nullable=False)
    rutgers_verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<User pk:{} email:{} name:{} pronouns:{}>".format(
            self.rums_pk, self.email, self.name, self.pronouns
        )


class Visit(db.Model):
    visit_pk = db.Column(db.Integer, primary_key=True)
    rums_pk = db.Column(db.Integer, db.ForeignKey("user.rums_pk"), nullable=True)
    card_pk = db.Column(db.String(20), db.ForeignKey("card.card_pk"), nullable=False)
    site_pk = db.Column(db.String(20), db.ForeignKey("site.site_pk"), nullable=False)
    entry_time = db.Column(
        db.DateTime, nullable=False, default=datetime.now(timezone.utc)
    )  # we need to set our source TZ to UTC.  For some reason.  hate this.
    exit_time = db.Column(
        db.DateTime, nullable=True, default=None
    )  # Must always update on exit or close for the day.
    granted = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return "<Visit {} {} {} {} SIGNED OUT:{}>".format(
            self.visit_pk, self.card_pk, self.entry_time, self.granted, self.exit_time
        )


# This allows us to have global site and visit tracking unique to a given site and stuff. That way Ag stuff doesn't interfere with Livi, etc.
class Site(db.Model):
    site_pk = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(20), nullable=False)
    short_name = db.Column(
        db.String(20), unique=True, nullable=False
    )  # This is unique for our admin interface to click stuff.
    allow_entry_without_profile = db.Column(db.Boolean, nullable=False, default=False)
    rutgers_active_only = db.Column(db.Boolean, nullable=False, default=False)
    # Allow_entry_w.o_profile is used to track site-specific sign-in where their visit
    # is recorded without a person ID so it can later be associated with a rums_pk.

    # This is useful to allow things like RUMakers visits without a complete profile.

    def __repr__(self):
        return "<Site %r>" % self.site_name


class SoloMembership(db.Model):
    membership_pk = db.Column(db.Integer, primary_key=True)
    site_pk = db.Column(db.Integer, db.ForeignKey("site.site_pk"), nullable=False)
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
    site_pk = db.Column(db.String(20), db.ForeignKey("card.card_pk"), nullable=False)
    human_name = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    admin_user = db.Column(db.Integer, db.ForeignKey("user.rums_pk"), nullable=True)

    def __repr__(self):
        return """<GroupMembership pk:{} readable_name:{}>""".format(
            self.membership_pk, self.human_name
        )


class GroupMember(db.Model):
    membership_pk = db.Column(db.Integer, primary_key=True)
    group_membership_pk = db.Column(
        db.ForeignKey("group_membership.membership_pk"), nullable=False
    )
    rums_pk = db.Column(db.Integer, db.ForeignKey("user.rums_pk"), nullable=False)

    def __repr__(self):
        return """<GroupMember pk:{} rums_pk:{}>""".format(
            self.membership_pk, self.rums_pk
        )
