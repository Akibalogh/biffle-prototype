import SEAPI
import pymongo
from pymongo import MongoClient

so = SEAPI.SEAPI(site="stackoverflow")

# NOTE: min_delay of 0.5 should be acceptable
# As of Feb 27 2013, there were 1.7M users on StackOverflow. Thus page limit around 30,000 should be acceptable
some_users = so.fetch("users", min_delay=0.5, page_limit=5000)

print "Download finished. Status: " + str(so.last_status)

connection = MongoClient()
db = connection.db
so_users = db.so_users

add_counter = 0
skip_counter = 0
no_em_counter = 0

for user in some_users:
	sid = user['account_id']
	
	try:
		email_hash = user['profile_image'][31:63]

		if(len(email_hash) < 32):
			#print "Unable to get email hash for id: " + str(sid) + " profile_image: " + user['profile_image']
			no_em_counter += 1
			email_hash = ""

	except KeyError:
		email_hash = ""
	
	try:
		location = user['location']
	except KeyError:
		location = ""

	try:
		web_url = user['website_url']
	except KeyError:
		web_url = ""

	
	so_user = [{ 	"sid": sid,
			"dn": user['display_name'],
			"eh": email_hash,
			"l": location,
			"w": web_url }]

	#print str(so_user)

	if (so_users.find( { "sid": sid } ).count() == 0):
		ret = so_users.insert(so_user)
		#print "Created so_user in db.so_users: " + str(sid)
		add_counter += 1
	else:
		skip_counter += 1
		#print "User with id " + str(sid) + " already exists! Record not inserted"


print "SO download complete! " + str(add_counter) + " users added to db.so_users"

if (add_counter > 0):
	print "Unable to get email hash for " + str(no_em_counter) + "/" + str(add_counter) + " users (" + str(float(float(no_em_counter) / float(add_counter)) * 100) + "%)"
