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
		pass

	if user.has_key('in'):
		# Add LinkedIn industry
		wordcloud.append(user['in'])

	if user.has_key('sk'):
		# Add LinkedIn skills
		for skill in user['sk']:
			#print user['e'], skill
			wordcloud.append(skill)

	# Get StackOverflow terms
	if user.has_key('ta'):
		for tag in user['ta'][0]:
			wordcloud.append(tag)
	if user.has_key('tq'):
		for tag in user['tq'][0]:
			wordcloud.append(tag)
	if user.has_key('tt'):
		for tag in user['tt'][0]:
			wordcloud.append(tag)

	# Upsert wordcloud into user
	print "Wordcloud with " + str(len(wordcloud)) + " elements added to " + user['e']
	ret = users.update({'e': user['e']},
	        {'$set': {'wc': wordcloud}},
	        upsert = True )

