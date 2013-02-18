import sys
import pymongo
from pymongo import MongoClient


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
	print "User count: ", users.count()
	print_user_keywords(users)
