from db.sqlite_store import *


def create_solo_membership(rums_pk, membership_name, membership_start, membership_end):
    rums_pk = int(rums_pk)
    memberships = query_db(
        """SELECT * FROM memberships WHERE rums_pk == {}""".format(rums_pk)
    )

    print(memberships)


def get_last_visits(num_visits=20):
    visits = query_db(
        """SELECT users.name, users.netid, users.email, visits.entry_time, visits.exit_time, visits.granted from visits 
		LEFT JOIN users 
		ON visits.rums_pk = users.rums_pk;"""
    )

    return visits


# Helper function to create the group memberships for students & faculty / staff.
# No expiry makes it perpetual, remove users from group membership whenever plausible.
#
# 	group_mem_name VARCHAR(20),
# 	start_date DATETIME NOT NULL,
# 	end_date DATETIME,
# 	admin_user_pk INT,
# 	human_name was removed, I did an oopsie.
#

# Start and end date should be in format 'YYYY-MM-DD HH:MM:SS'.
def create_group_membership(membership_name, start_date, admin_user_pk, end_date=None):
    query_db(
        """INSERT INTO group_memberships 
	(group_mem_name, start_date, admin_user_pk) 
	VALUES ("{}", datetime('{}'), {}, "{}")""".format(
            membership_name, start_date, admin_user_pk
        )
    )

    # We set the end date in a subsequent query due to the lack of easy wrapper for SQLite using the query_db method.
    # This sensibly should be all torn out and replaced with an ORM but it's crustier... by a lot.
    if end_date != None:
        query_db(
            """UPDATE group_memberships 
		SET end_date = datetime('{}')
		WHERE group_mem_name = {} 
		AND start_date = datetime('{}') 
		ORDER BY group_mem_pk DESC;""".format(
                end_date, membership_name, start_date
            ),
            one=True,
        )


def create_user(
    cardNo,
    user_name,
    user_netid,
    user_email,
    membership_start,
    membership_end,
    membership_name,
):

    x = """INSERT INTO users (netid, email, name) VALUES ("{}","{}","{}");""".format(
        (user_netid),
        (user_email),
        (user_name),
    )
    cardInsert = query_db(x)

    rums_pk = """SELECT rums_pk FROM users WHERE email = "{}" ORDER BY rums_pk DESC;""".format(
        user_email
    )  # we need the rums pk to insert the card.

    print(query_db(rums_pk))


def card_in_use(cardNo):

    print(cardNo)
    cardNo = str(int(str(cardNo)))  # gets rid of any extra zeroes.

    print(cardNo)
    cardsMatching = query_db(
        """SELECT * from cards where card_no = "{}";""".format(cardNo)
    )

    from pprint import pprint

    if len(cardsMatching) == 0:
        return None

    cardsMatching = cardsMatching[0]

    userMatch = query_db(
        """SELECT * FROM users where rums_pk = {}""".format(cardsMatching[0])
    )

    print(userMatch)
    return userMatch[0]


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
