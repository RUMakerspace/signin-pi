import sqlite3
from flask import g

DATABASE = "./db/visits.db"

###
# Helper functions to create our schemas if they don't exist yet.
###

# This is to keep track of sites (Livingston, Honors College, Ag, etc.  Used to generate automatic memberships for students / faculty and lets us distinguish visits.

create_table_sites = """
CREATE TABLE IF NOT EXISTS users ( 
	site_pk INTEGER PRIMARY KEY AUTOINCREMENT,
	site_name VARCHAR(20) NOT NULL UNIQUE,
	short_name VARCHAR(20) NOT NULL;
);

"""
create_table_users = """
CREATE TABLE IF NOT EXISTS users ( 
	rums_pk INTEGER PRIMARY KEY AUTOINCREMENT,
   	netid VARCHAR(20),
	email VARCHAR(50) NOT NULL,
	name VARCHAR(50) NOT NULL,
	zk_pk INT UNIQUE
);

"""

# This table keeps track of fobs / RUID card numbers.  the VARCHAR(20)
#  field is because we may need to store zero-prepended
# card numbers for future use.

create_table_cards = """
CREATE TABLE IF NOT EXISTS cards ( 
	card_pk INTEGER PRIMARY KEY AUTOINCREMENT,
	rums_pk INT,
	card_no VARCHAR(20) UNIQUE NOT NULL
);

"""

# This is for individual memberships, such as a user paying for one at Ag.

create_table_memberships = """
CREATE TABLE IF NOT EXISTS memberships ( 
	membership_pk INTEGER PRIMARY KEY AUTOINCREMENT,
   	rums_pk INT,
	start_date DATETIME NOT NULL,
	end_date DATETIME,
	human_name VARCHAR(20)
);

"""

# rums_pk can only be null because we want to allow non-set-up members to sign in now and set up later.
# This is useful for things like RUMakers where we want to expedite their visit association.

# We should still add their card to the card list if possible, otherwise visits will become a dumping ground...
# Maybe sensible?
create_table_visits = """
CREATE TABLE IF NOT EXISTS visits ( 
	visit_pk INTEGER PRIMARY KEY AUTOINCREMENT,
   	rums_pk INT,
	card_no VARCHAR(20) NOT NULL,
	entry_time DATETIME NOT NULL,
	exit_time DATETIME,
	granted INT NOT NULL
);

"""

create_table_group_memberships = """
CREATE TABLE IF NOT EXISTS group_memberships ( 
	group_mem_pk INTEGER PRIMARY KEY AUTOINCREMENT,
	group_mem_name VARCHAR(20),
	start_date DATETIME NOT NULL,
	end_date DATETIME,
	admin_user_pk INT
);

"""

create_table_group_members = """
CREATE TABLE IF NOT EXISTS group_members ( 
	group_member_pk INTEGER PRIMARY KEY AUTOINCREMENT,
	group_membership_pk INT NOT NULL,
	rums_pk INT NOT NULL
);

"""

sqlite_tables = [
    create_table_sites,
    create_table_group_members,
    create_table_cards,
    create_table_group_memberships,
    create_table_visits,
    create_table_users,
    create_table_memberships,
]


def setupTables():
    for tableDat in sqlite_tables:
        query_db(tableDat)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    get_db().commit()
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv
