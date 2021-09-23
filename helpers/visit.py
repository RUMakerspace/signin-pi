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


def createVisit(rums_pk, card_pk, site_pk, granted):
    tempVisit = Visit(
        rums_pk=rums_pk, card_pk=card_pk, site_pk=site_pk, granted=granted
    )
    tempVisit.entry_time = datetime.utcnow()

    if (not granted) or (granted == 0):
        tempVisit.exit_time = (
            tempVisit.entry_time
        )  # Impossibly short visit for entries not possible.
    db.session.add(tempVisit)
    db.session.commit()
    return tempVisit


# This function will return true IIF the current user is signed in at our site but isn't
# yet signed out.  it will be useful for our periodic checks and also to try and sign
# people out without any of the other fancy stuff for sign-in.
def userIsAtSite(rums_pk, site_pk):
    visits = Visit.query.filter(
        (Visit.rums_pk == rums_pk)
        and (Visit.site_pk == site_pk)
        and (exit_time is None)
    )

    if visits.count() > 0:
        return True
    return False


def signUserOut(rums_pk, site_pk):
    visits = Visit.query.filter(
        (Visit.rums_pk == rums_pk)
        and (Visit.site_pk == site_pk)
        and (exit_time is None)
    )

    currentVisit = visits.first()
    # we assume we can only have one ongoing visit,
    # otherwise it'd sign them out. may need to
    # work on auto-signout code though.

    currentVisit.exit_time = datetime.utcnow()
    db.session.commit()
