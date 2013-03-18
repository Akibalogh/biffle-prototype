import pymongo
from pymongo import MongoClient

users = MongoClient().db.users


for user in users.find():
	wordcloud = []

	try:
		# Add digital footprint terms from FullContact
		for term in user['fc']['digitalFootprint']['topics']:
			wordcloud.append(term['value'])
	except KeyError:
		continue

	if user.has_key('in'):
		# Add LinkedIn industry
		wordcloud.append(user['in'])

	if user.has_key('sk'):
		# Add LinkedIn skills
		for skill in user['sk']:
			wordcloud.append(skill)

	# Get StackOverflow terms
	if user.has_key('ta'):
		wordcloud += user['ta'][0]
	if user.has_key('tq'):
		wordcloud += user['tq'][0]
	if user.has_key('tt'):
		wordcloud += user['tt'][0]

	# Upsert wordcloud into user
	ret = users.update({'e': user['e']},
	        {'$push': {'wc': wordcloud}},
	        True )

