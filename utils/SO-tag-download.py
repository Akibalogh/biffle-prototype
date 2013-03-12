import SEAPI
import pymongo
from pymongo import MongoClient
import hashlib

connection = MongoClient()
users = conncetion.db.users
so_users = connection.perm.so_users

api_key = "F9V4YsNAO1aBrgFRZlReWQ(("
#api_key = ""

so = SEAPI.SEAPI(api_key, site="stackoverflow")
found_counter = 0
not_found_counter = 0

for user in users.find(): 
	email_hash = hashlib.md5(user['e']).hexdigest()
	found_user = None
        found_user = so_users.find_one( { "eh" : email_hash } )
	print found_user
        if (found_user is not None):
        	print "Found user! e: " + user['e'] + " hash: " + str(found_user['eh'])
		print "Fetching tags for sid: " + str(found_user['sid'])
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

