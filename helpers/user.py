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


def userExists(cardNo):
    currentCard = Card.query.filter(Card.card_no == cardNo)

    if currentCard.count() == 0:
        q = createShadowUserByCardNo(cardNo)
        db.session.add(q)
        db.session.commit()

        return q

    if currentCard.first().rums_pk != None:
        currentUser = User.query.filter(
            User.rums_pk == currentCard.first().rums_pk
        ).first()
        return currentUser


def addCardToUser(cardNo, rums_pk):
    tempCard = Card.query.filter(Card.card_no == cardNo).first()

    tempUser = User.query.filter(User.rums_pk == rums_pk).first()

    tempCard.rums_pk = tempUser.rums_pk
    db.session.commit()


# This function gets us a internal user object for any netID or email (unique in both cases)
# such that we can assign new cards to old users easily.


def setupUserExists(netid=None, email=None):
    if netid == None and email == None:
        raise Error("Cannot have netID *and* email be null.")

    # Get any user with the right netID and it isn't None *or* the right email.
    # May be redundant, not 100% sure.  We absolutely check that it's not a shadow
    # profile because despite our best effort, the DB may still be manually edited.

    matchUser = User.query.filter(
        (
            ((User.netid == netid) & (User.netid != None))
            | ((User.email == email) & (User.email != None))
        )
        & (User.shadow_profile == 0)
    ).first()

    print(matchUser)

    return matchUser


def createShadowUserByCardNo(cardNo):
    print("Card Number to be made:{}".format(cardNo))

    cardNo = str(int(str(cardNo)))

    tempUser = User(shadow_profile=True)
    print("user created")

    db.session.add(tempUser)
    db.session.commit()

    tempCard = Card(card_no=cardNo, rums_pk=tempUser.rums_pk)

    db.session.add(tempCard)
    db.session.commit()

    return tempUser
