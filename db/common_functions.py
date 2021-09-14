from db.sqlite_store import *


def create_solo_membership(rums_pk, membership_name, membership_start, membership_end):
    rums_pk = int(rums_pk)
    memberships = query_db(
        """SELECT * FROM memberships WHERE rums_pk == {}""".format(rums_pk)
    )

    print(memberships)


def get_last_visits(num_visits=20):
    # visits = query_db("""SELECT b.name, b.netid, b.email, a.rums_pk, a.card_no, b.ROW_NUMBER() OVER (), a.entry_time, a.exit_time, a.granted FROM visits a INNER JOIN users b ON a.rums_pk = b.ROW_NUMBER();""".format(num_visits))

    visits = query_db(
        """SELECT users.name, users.netid, users.email, visits.entry_time, visits.exit_time, visits.granted from visits LEFT JOIN users ON visits.rums_pk = users.rums_pk;"""
    )

    # print(len(visits))
    # visits = query_db("""SELECT rowid, * from users;""")
    return visits


def create_fake_users(num=20):
    import random
    import string

    for i in range(num):
        netIDPref = "".join(random.choice(string.ascii_lowercase) for i in range(3))
        endNo = "".join(random.choice(string.digits) for i in range(4))
        x = """INSERT INTO users (netid, email, name) VALUES ("{}","{}","{}");""".format(
            ("" + netIDPref + endNo),
            ("" + netIDPref + endNo + """@rutgers.edu"""),
            netIDPref[::-1],
        )
        print(x)

        query_db(x)


def create_fake_cards(num=25):
    import random
    import string

    users = query_db("""SELECT rums_pk FROM users LIMIT 20;""")
    users = [x[0] for x in users]

    for u in users:
        cardNoTemp = "".join(random.choice(string.digits) for i in range(12))
        query_db(
            """INSERT INTO cards (rums_pk, card_no) VALUES ({}, "{}")""".format(
                u, cardNoTemp
            )
        )

    for i in range(num - len(users)):
        tempUser = random.choice(users)
        cardNoTemp = "".join(random.choice(string.digits) for i in range(12))
        query_db(
            """INSERT INTO cards (rums_pk, card_no) VALUES ({}, "{}")""".format(
                tempUser, cardNoTemp
            )
        )


def create_fake_visits(num=50):
    import random
    import string

    cards = query_db("""SELECT * FROM cards;""")
    for k, c in enumerate(cards):
        print(c)
        if k % 2 == 0:
            exitStr = "null,"
        else:
            exitStr = """datetime('now'),"""

        query_db(
            """INSERT INTO visits (rums_pk, card_no, entry_time, exit_time, granted) VALUES ({}, "{}", datetime('now'), {} 1)""".format(
                c[0], c[1], exitStr
            )
        )
