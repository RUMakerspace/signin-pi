from db.sqlite_store import *

def create_solo_membership(rums_pk, membership_name, membership_start, membership_end):
	rums_pk = int(rums_pk)
	memberships = query_db("""SELECT * FROM memberships WHERE rums_pk == {}""".format(rums_pk))
	
	print(memberships)
	
def get_last_visits(num_visits=20):
	#visits = query_db("""SELECT b.name, b.netid, b.email, a.rums_pk, a.card_no, b.ROW_NUMBER() OVER (), a.entry_time, a.exit_time, a.granted FROM visits a INNER JOIN users b ON a.rums_pk = b.ROW_NUMBER();""".format(num_visits))
	
	visits = query_db("""SELECT users.name, users.netid, visits.rums_pk, visits.entry_time, visits.exit_time, visits.granted from visits LEFT JOIN users ON visits.rums_pk = users.rowid;""") 
	from pprint import pprint
	#print(len(visits))
	#visits = query_db("""SELECT rowid, * from users;""")
	pprint(visits)
	return visits
	
def create_fake_users(num=20):
	import random
	import string
	
	for i in range(num):
		netIDPref = ''.join(random.choice(string.ascii_lowercase) for i in range(3))
		endNo = ''.join(random.choice(string.digits) for i in range(4))
		x = ("""INSERT INTO users (netid, email, name) VALUES ("{}","{}","{}");""".format(("" + netIDPref + endNo), ("" + netIDPref + endNo + """@rutgers.edu"""), netIDPref[::-1]))
		print(x)
		
		query_db(x)