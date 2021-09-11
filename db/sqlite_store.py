import sqlite3
from flask import g

DATABASE = "./db/visits.db"

###
# Helper functions to create our schemas if they don't exist yet.
###

create_table_users = """
CREATE TABLE IF NOT EXISTS users ( 
   	netid VARCHAR(20),
	email VARCHAR(50) NOT NULL,
	name VARCHAR(50) NOT NULL,
	zk_pk INT UNQIUE
);

"""

create_table_cards = """
CREATE TABLE IF NOT EXISTS cards ( 
	rums_pk INT,
	card_no VARCHAR(20) UNIQUE NOT NULL
);

"""

create_table_memberships = """
CREATE TABLE IF NOT EXISTS memberships ( 
   	rums_pk INT,
	start_date DATETIME NOT NULL,
	end_date DATETIME,
	human_name VARCHAR(20)
);

"""

create_table_visits = """
CREATE TABLE IF NOT EXISTS visits ( 
   	rums_pk INT NOT NULL,
	card_no VARCHAR(20) NOT NULL,
	entry_time DATETIME NOT NULL,
	exit_time DATETIME,
	granted INT NOT NULL
);

"""

create_table_group_memberships = """
CREATE TABLE IF NOT EXISTS group_memberships ( 
	group_mem_name VARCHAR(20),
	start_date DATETIME NOT NULL,
	end_date DATETIME,
	admin_user_pk INT,
	human_name VARCHAR(20)
);

"""

create_table_group_member_users = """
CREATE TABLE IF NOT EXISTS group_members ( 
	group_membership_pk INT NOT NULL,
	rums_pk INT NOT NULL
);

"""

sqlite_tables = [
    create_table_group_member_users,
    create_table_cards,
    create_table_group_memberships,
    create_table_visits,
    create_table_users,
    create_table_memberships,
]


def setupTables():
    for tableDat in tabLES:
        query_db(tableDat)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv
