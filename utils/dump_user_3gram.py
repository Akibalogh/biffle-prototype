import sys
import os
import pymongo
from pymongo import MongoClient

def print_user_keywords(users, outfile_name):
	# make a list of keywords user is interested in
	for user in users:
		user_recognized_keywords = user['k']
		user_skills = user['sk']

		try:
			user_klout_keywords = [ x['value'] for x in user['fc']['digitalFootprint']['topics'] ]
		except KeyError:
			user_klout_keywords = []

		try:
			user_SO_tq = user['tq'][0]
		except KeyError:
			user_SO_tq = []

		try:
			user_SO_tt = user['tt'][0]
		except KeyError:
			user_SO_tt = []

		try:
			user_SO_ta = user['ta'][0]
		except KeyError:
			user_SO_ta = []

		# 'wc' Wordcloud contains all keywords but no information about where they came from
		#try:
		#	user_keywords = list(set( user['wc'][0] ))
		#except KeyError:
		#	pass

		# 'k' Only designates the keywords that Biffle recognized from its (limited) vocabulary
		#for k in user_recognized_keywords:
		#	print user['e'] + '\t' + 'recognized keyword' + '\t' + k + '\t'

		with open(outfile_name, 'a') as outfile:

	                for k in user_skills:
				outfile.write(user['e'] + '\t' + 'LI-skill' + '\t' + k + '\t' + '\n')

			for k in user_klout_keywords:
				outfile.write(user['e'] + '\t' + 'Klout' + '\t' + k + '\t' + '\n')

	                for k in user_SO_tq:
        	                outfile.write(user['e'] + '\t' + 'SO_tq' + '\t' + k + '\t' + '\n')

	                for k in user_SO_tt:
        	                outfile.write(user['e'] + '\t' + 'SO_tt' + '\t' + k + '\t' + '\n')

	                for k in user_SO_ta:
        	                outfile.write(user['e'] + '\t' + 'SO_ta' + '\t' + k + '\t' + '\n')


if __name__ == "__main__":
	# Connect to MongoDB
	connection = MongoClient()
	db = connection.db
	users = db.users.find()
	so_users = db.so_users
	print "User count: ", users.count()
	outfile_name = '3gram-keyword-dump'
	
	if (os.path.exists(outfile_name)):
		os.remove(outfile_name)
	
	print_user_keywords(users, outfile_name)
