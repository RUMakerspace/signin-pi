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


def getAllMemberships(rums_pk):
    currentDateTime = datetime.utcnow()  # To do the filter comparison.
    currentUser = User.query.filter_by(rums_pk=int(rums_pk)).first()

    outputList = []

    tempItem = {"name": "", "start": "", "end": ""}

    soloType = SoloMembership.query.filter(
        SoloMembership.rums_pk == currentUser.rums_pk
    )
    for s in soloType:
        intTemp = tempItem.copy()
        intTemp["name"] = s.human_name
        intTemp["start"] = s.start_date.strftime("%Y/%m/%d")
        if s.start_date != None:
            intTemp["end"] = s.start_date.strftime("%Y/%m/%d")
        else:
            intTemp["end"] = None

        outputList.append(intTemp)

    groupType = (
        db.session.query(GroupMember, GroupMembership)
        .filter(GroupMember.rums_pk == currentUser.rums_pk)
        .all()
    )

    for s in groupType:
        print(dir(s))
        intTemp = tempItem.copy()
        intTemp["name"] = s.GroupMembership.human_name
        intTemp["start"] = s.GroupMembership.start_date.strftime("%Y/%m/%d")
        if s.GroupMembership.start_date != None:
            intTemp["end"] = s.GroupMembership.start_date.strftime("%Y/%m/%d")
        else:
            intTemp["end"] = None

        outputList.append(intTemp)

    outputList = sorted(outputList, key=lambda x: x["end"], reverse=True)
    return outputList


def allowEntry(rums_pk, site_pk):
    currentUser = User.query.filter_by(rums_pk=int(rums_pk))

    currentUser = currentUser.first()

    print("Found user\t{}".format(currentUser))

    currentSite = Site.query.filter_by(site_pk=site_pk).first()

    if currentUser.rutgers_active:
        return True  # Allow, rutgers community.
    else:
        if currentSite.rutgers_active_only:
            return False  # deny, site is for only rutgers community.
        else:
            return hasValidMembership(
                # if the site is for anyone but the
                # user isn't rutgers, explicitly
                # check memberships.
                currentUser,
                currentSite,
            )  # check valid site memberships.


def hasValidMembership(currentUser, currentSite):
    currentDateTime = datetime.utcnow()  # To do the filter comparison.

    # This will get us only valid solo memberships
    # after right now that haven't expired yet and
    # are for this site type.

    soloType = SoloMembership.query.filter(
        SoloMembership.rums_pk == currentUser.rums_pk
        and SoloMembership.start_date >= currentDateTime
        and (
            (SoloMembership.end_date <= currentDateTime)
            or (SoloMembership.end_date == None)
        )
        and (SoloMembership.site_pk == currentSite.site_pk)
    )

    print(soloType.first())

    groupType = GroupMember.query.join(
        GroupMembership,
        GroupMember.group_membership_pk == GroupMembership.membership_pk,
    ).filter(
        GroupMember.rums_pk == currentUser.rums_pk
        and GroupMembership.start_date >= currentDateTime
        and (
            (GroupMembership.end_date <= currentDateTime)
            or (GroupMembership.end_date == None)
        )
        and (GroupMembership.site_pk == currentSite.site_pk)
    )

    if soloType.count() + groupType.count() > 0:
        return True
    return False

    # groupType = list(GroupMember.query.filter_by(rums_pk=rumspk))
