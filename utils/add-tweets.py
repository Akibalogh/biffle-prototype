import pymongo
from pymongo import MongoClient
import requests
import simplejson

connection = MongoClient()
db = connection.db
users = db.users
user_tweets = db.user_tweets

for user in users.find():
	# Get twitter_ids for users
	twitter_id = None
	if 'socialProfiles' in user['fc']:	
		for socialProfile in user['fc']['socialProfiles']:
			if (socialProfile['type'] == 'twitter'):
				twitter_id = socialProfile['id']
	elif 'socialProfile' in user['fc']:
		if (user['fc']['socialProfile']['type'] == 'twitter'):
			twitter_id = user['fc']['socialProfile']['id']

	twitter_timeline_api_url = 'https://api.twitter.com/1/statuses/user_timeline.json'

	# If the user doesn't have a Twitter ID, then go to the next user
	if (twitter_id is None):
		continue

	# Get the first 200 tweets
	twitter_params = dict(user_id=twitter_id, include_entities=0, include_rts=1, count=200)
	twitter_req = requests.get(twitter_timeline_api_url, params=twitter_params)

	# Initialize object containing all tweets
	all_tweets = [ x['text'] for x in twitter_req.json ]
	t_max_id = 0

	# Get the next 3,000 tweets (3,200 total allowed by Twitter API)
	for i in range (1, 16):
		# Get max ID
		ids = []
		for tweet in twitter_req.json:
			id = tweet['id']
			ids.append(id)
			if (t_max_id < id):
				t_max_id = id

		twitter_params = dict(user_id=twitter_id, include_entities=0, include_rts=1, count=200, max_id=t_max_id)
		twitter_req = requests.get(twitter_timeline_api_url, params=twitter_params)

		print "Getting tweets for " + user['e'] + ". Page: " + str(i)
		all_tweets += [ x['text'] for x in twitter_req.json ]


		# TODO: If Twitter stops returning tweets, exit loop

	user_tweets.update(     { 'e': user['e'] },
				{ '$push': { 't': { '$each':  all_tweets } } },
				True )

