import sys
import pymongo
from pymongo import MongoClient
import hashlib

def print_user_keywords(users):
	# make a list of keywords users interested in
	user_keywords=[]
	for u in users:
		user_keywords=user_keywords+ u['k']
	user_keywords=list(set(user_keywords))
	print user_keywords

if __name__ == "__main__":
	# Connect to MongoDB
	connection = MongoClient()
	db = connection.db
	users = db.users.find()
	so_users = db.so_users
	# print "User count: ", users.count()
	# print_user_keywords(users)

	found_counter = 0
	not_found_counter = 0

	for user in users:
		email_hash = hashlib.md5(user['e']).hexdigest()
		#print "e: " + user['e'] + " hash: " + email_hash

		found_user = None
		found_user = so_users.find_one( { "eh" : email_hash } )
		if (found_user is not None):
			print "Found user! e: " + user['e'] + " hash: " + str(found_user['eh'])
			found_counter += 1
		else:
			#print "Did not find user e: " + user['e']
			not_found_counter += 1

	found_percent = float(found_counter) / float(not_found_counter) * 100
	print "Found: " + str(found_counter) + "/" + str(found_counter + not_found_counter) + " (" + "{0:.0f}".format(found_percent) + "%)"
