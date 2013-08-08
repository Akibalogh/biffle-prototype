import sys
import os
from os import listdir
from os.path import isfile, join
from lxml import etree
#import lxml.html, lxml.html.clean
import pymongo
from pymongo import MongoClient
import requests
import simplejson

import local_passwords
FULLCONTACT_API_KEY = local_passwords.FULLCONTACT_API_KEY


default_path = '/data/profiles'

if len(sys.argv) < 2:
	print 'Usage: python profile-parse.py <input-file(s)>'
	print 'Input file not specified. Using ' + default_path
	profile_file_list = [ join(default_path,f) for f in listdir(default_path) if isfile(join(default_path,f)) ]
else:
	profile_file_list = sys.argv[1:]

# Connect to MongoDB
connection = MongoClient()
db = connection.db
users = db.users

fullcontact_api_key = FULLCONTACT_API_KEY

for infile_name in profile_file_list:
	# Open file and load lxml parser
	print 'Parsing profile: ' + infile_name
	infile = open(infile_name, "r")
	readprofile = infile.read()
	inprofile = etree.fromstring(readprofile)

	# Populate commonly-used fields
	id = inprofile.find("id").text
	name = inprofile.find("first-name").text + inprofile.find("last-name").text
	industry = inprofile.find("industry").text
	email = inprofile.find("email-address").text

	# Take only subset of entire LinkedIn profile
	# Currently taking profile summary, job summaries and skill names
	interests = []
	skills = []

	if (inprofile.findall("summary") != []):
		interests.append(inprofile.find("summary").text)
	
	positions = inprofile.xpath('//positions/position/summary/text()')
	for position in positions:
		interests.append(position.encode('ascii', 'ignore'))

	profile_skills = inprofile.xpath('//skills/skill/skill/name/text()') # Note: two nested skill tags
	for skill in profile_skills:
		skills.append(skill.encode('ascii', 'ignore'))

	# Pull in data from FullContact API
	fc_params = dict(apiKey = fullcontact_api_key, email = email)
	fc_request = requests.get('https://api.fullcontact.com/v2/person.json', params=fc_params)
	full_contact_info = simplejson.loads(fc_request.text)

	#print [str(item) + ' ' +  str(type(item)) for item in interests]

	# Use files with terms in them to parse
	# TODO: Add support for semantic webs of terms
	path = "/root/biffle-prototype/wordclouds"
	file_list = [ f for f in listdir(path) if isfile(join(path,f)) ]

	wordcloud = []
	for file in file_list:
		wordcloud.append(open(path + "/" + file, 'r').read().splitlines())

	# Initialize empty keyword list
	keywords = []

	for terms in wordcloud:
		for term in terms:
			# Match terms from interests or skills (regardless of case)
			lowercase_term = term.lower()
			lowercase_interests = [item.lower() for item in interests]
			lowercase_skills = [item.lower() for item in skills]
			# TODO: Pull in lowercase Klout tags

			if ((lowercase_term in lowercase_interests) or (lowercase_term in lowercase_skills)):
				if (not term in keywords): keywords.append(term)

	user = [{
		"lid": id,
		"e": email,
		"ln": interests,
		"sk": skills,
		"in": industry,
		"k": keywords,
		"opt": industry,
		"fc": full_contact_info
		}]

	# Check if user record already exists in MongoDB
	ret = users.update(
                       {'e': email},
                       { 
                         "lid": id,
                         "e": email,
                         "ln": interests,
                         "sk": skills,
                         "in": industry,
                         "k": keywords,
                         "opt": industry,
                         "fc": full_contact_info
                       },
                       True)

	print "Upserted user to db.users: " + email


