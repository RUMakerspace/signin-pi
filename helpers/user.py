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
