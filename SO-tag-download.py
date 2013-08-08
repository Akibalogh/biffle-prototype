import sys
sys.path.append('utils') # Look in utils for SEAPI
import SEAPI
import pymongo
from pymongo import MongoClient
import hashlib

import local_passwords
SO_API_KEY = local_passwords.SO_API_KEY

connection = MongoClient()
users = connection.db.users
so_users = connection.perm.so_users

api_key = SO_API_KEY

so = SEAPI.SEAPI(api_key, site="stackoverflow")
found_counter = 0
not_found_counter = 0

print "Enriching user objects with StackOverflow tags"

for user in users.find(): 
	email_hash = hashlib.md5(user['e']).hexdigest()
	found_user = None
        found_user = so_users.find_one( { "eh" : email_hash } )
        if (found_user is not None):
        	print "Fetching tags for user e: " + user['e'] + " hash: " + str(found_user['eh'])
		tags_json = so.fetch_one("users/{id}/tags", id=found_user['sid'])
		top_answer_tag_json = so.fetch_one("users/{id}/top-answer-tags", id=found_user['sid'])
		top_question_tag_json = so.fetch_one("users/{id}/top-question-tags", id=found_user['sid'])

		tags = []
		for tag in tags_json:
			tags.append(tag['name'])

		top_answer_tags = []
		for tag_a in top_answer_tag_json:
			top_answer_tags.append(tag_a['tag_name'])

		top_question_tags = []
		for tag_q in top_question_tag_json:
			top_question_tags.append(tag_q['tag_name'])

		ret = users.update({'e': user['e']},
				   {'$push': {'tt': tags, 'ta': top_answer_tags, 'tq': top_question_tags}},
				   True)
                found_counter += 1
        else:
                print "Did not find user e: " + user['e']
                not_found_counter += 1

found_percent = float(found_counter) / float(found_counter + not_found_counter) * 100
print "Found: " + str(found_counter) + "/" + str(found_counter + not_found_counter) + " (" + "{0:.0f}".format(found_percent) + "%)"

