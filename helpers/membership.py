from model.datastore import (
    db,
    Visit,
    SoloMembership,
    GroupMembership,
    GroupMember,
    Card,
    Site,
    User,
)
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


def allowEntry(rums_pk, site_pk):
    currentUser = User.query.filter_by(rums_pk=int(rums_pk))

    currentUser = currentUser.first()

    print(currentUser)

    currentSite = Site.query.filter_by(site_pk=site_pk).first()

    if currentUser.rutgers_active:
        return True  # Allow, rutgers community.
    else:
        if currentSite.rutgers_active_only:
            return False  # deny, site is for only rutgers community.
        else:
            return hasValidMembership(rums_pk, site_pk)  # check valid site memberships.


def hasValidMembership(rums_pk, site_pk):
    currentDateTime = datetime.utcnow()  # To do the filter comparison.

    # XXX TODO, this does not work.
    soloType = (
        SoloMembership.query.filter_by(rums_pk=rums_pk)
        .filter_by(SoloMembership.start_date >= currentDateTime)
        .filter_by(SoloMembership.end_date <= currentDateTime)
    )

    print(soloType)
    groupType = list(GroupMember.query.filter_by(rums_pk=rums_pk))
