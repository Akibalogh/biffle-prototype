import SEAPI
import pymongo
from pymongo import MongoClient
import hashlib

connection = MongoClient()
db = connection.db
users = db.users
so_users = db.so_users

#api_key = "F9V4YsNAO1aBrgFRZlReWQ(("
api_key = ""
so = SEAPI.SEAPI(api_key, site="stackoverflow")

# NOTE: min_delay of 0.5 should be acceptable
# As of Feb 27 2013, there were 1.7M users on StackOverflow. Thus page limit around 30,000 should be acceptable
# To make less than 10,000 API requests per day, set the delay to 10 seconds (max delay 8.64s)
so_fetched_users = so.fetch("users", db, min_delay=0.5, page_limit=5)
#so_fetched_users = so.fetch("users", db, min_delay=10, page_limit=30000)

print "Download and insert finished"
#print "Status: " + str(so.last_status)

user_counter = so_users.find().count()
no_em_counter = so_users.find({ "eh": "" }).count()
found_counter = 0
not_found_counter = 0

if (user_counter > 0):
	print "Unable to get email hash for " + str(no_em_counter) + "/" + str(user_counter) + " users (" + "{0:.1}".format(str(float(float(no_em_counter) / float(user_counter)) * 100)) + "%)"

for user in users.find(): 
	email_hash = hashlib.md5(user['e']).hexdigest()
	found_user = None
        found_user = so_users.find_one( { "eh" : email_hash } )
        if (found_user is not None):
        	print "Found user! e: " + user['e'] + " hash: " + str(found_user['eh'])
		print "SID: " + str(found_user['sid'])
		tags = so.fetch_one("users/{id}/tags", id=found_user['sid'])
		top_answer_tags = so.fetch_one("users/{id}/top-answer-tags", id=found_user['sid'])
		top_question_tags = so.fetch_one("users/{id}/top-question-tags", id=found_user['sid'])
		ret = users.update({'e': user['e']},
				   {'$push': {'tt': tags, 'ta': top_answer_tags, 'tq': top_question_tags}},
				   True)
                found_counter += 1
        else:
                print "Did not find user e: " + user['e']
                not_found_counter += 1

found_percent = float(found_counter) / float(found_counter + not_found_counter) * 100
print "Found: " + str(found_counter) + "/" + str(found_counter + not_found_counter) + " (" + "{0:.0f}".format(found_percent) + "%)"

