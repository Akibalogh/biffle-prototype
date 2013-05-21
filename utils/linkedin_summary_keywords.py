import pymongo
from pymongo import MongoClient
from textrank import textrank

def linkedin_summary(user):
	text = ''
	for line in user['ln']:
		text += ' ' + line
	return textrank(text)

