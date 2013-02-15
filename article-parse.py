import sys

# Add path for textrank
sys.path.append("/root/textrank/")
from textrank import textrank

import os
from os import listdir
from os.path import isfile, join
import datetime
from datetime import datetime
import string
import pymongo
from pymongo import MongoClient
import base64
import lxml.html, lxml.html.clean
from lxml import etree
import urllib2
import re
import random

def download_article_file(articleURL, articleFileDirectory, code):
	articleFilePath = articleFileDirectory + code
				
	# Download the article and save as file
	if (articleURL == ""):
		print "Empty URL detected! File not created"
		return None
	else:
		# If a directory for files doesn't exist, create it
		dir = os.path.dirname(articleFileDirectory)

		if not os.path.isdir(dir):
			print "Created directory: " + dir
			os.makedirs(dir)
		
		try:
			fullArticle = urllib2.urlopen(articleURL)
			outfile = open(articleFilePath, 'w+')
			fullArticleText = fullArticle.read()
			outfile.write(fullArticleText)
			outfile.close

			# Use lxml's HTML cleaner to remove markup
			htmltree = lxml.html.fromstring(fullArticleText)		
			cleaner = lxml.html.clean.Cleaner(remove_unknown_tags=True)
			cleaned_tree = cleaner.clean_html(htmltree)
			return cleaned_tree.text_content()
	

		except urllib2.HTTPError, urllib2.URLError:
			print "File download skipped: " + articleURL	
			return None


def recommend_articles(db):
	recommended_articles = db.recommended_articles
	users = db.users
	articles = db.articles

	# For all users, recommend 5 articles
	for user in users.find():

		print "Making recommendations for user " + str(user['e'])
		potential_article_matches = []
		
		# Find all articles that match the user's keywords
		for keyword in user['k']:
			# Regex approximate match for string containing keyword -- similar to SQL LIKE
			# TODO: Implement exact match for keyword
			article_matches = articles.find({ "k": { "$regex": ".*" + re.escape(keyword) + ".*" } })
	
			for match in article_matches:
				print "Potential match! " + user['e'] + " could get " + str(match['_id'])
				potential_article_matches.append(match['_id'])
		
		# Make max 5 recommendations
		recommendations_to_make = min(5, len(potential_article_matches)) 
		recommendations_made = 0

		# Pick articles at random
		while (recommendations_made <= recommendations_to_make):
			if (len(potential_article_matches) == 0):
				print "No more articles to recommend to " + user['e']
				recommendations_made = (recommendations_to_make + 1)
				continue
		
			# Random is base-1 while pop is base-0
			random_num = random.randrange(1,len(potential_article_matches) + 1)
			chosen_article_id = potential_article_matches.pop(random_num - 1)

			chosen_article = articles.find_one( { "_id": chosen_article_id })
			chosen_article_title = chosen_article['t']
			chosen_article_title = chosen_article_title.encode('ascii', 'ignore')

			# Check that articles haven't been sent previously
			if (recommended_articles.find( { "uid": user['_id'], "aid": chosen_article_id } ).count() != 0):
				print "Article was recommended to " + user['e'] + " in the past. Ignore (" + chosen_article_title + ")"
				pass
			else:
				# Put the article in recommended articles
				recommended_article = [{
					"uid": user['_id'],
					"aid": chosen_article_id,
					"rt": datetime.today(),
					#"ct": click_datetime,
					#"st": save_datetime,
					"uk": user['k'],
					#"pk": presented_keywords,
					#"lt": like_datetime,
					#"sit": share_datetime,
				}]

				recommended_article_id = recommended_articles.insert(recommended_article)
				print "Recommended: " + chosen_article_title
				recommendations_made += 1


def parse_urls(db, base_directory, query):
	# Note: Assumes that path is stored as <query>.php/
	path = base_directory + query + ".php" + "/"
	
	file_list = [ f for f in listdir(path) if isfile(join(path,f)) ]

	articles = db.articles

	# For each file, get the article Titles and URLs
	for file in file_list:
		# Clear out any variables from last file
		articleURL = articleTitle = articleSource = summaryText = keywords = score = code = ""
		
		intext = open(path + file, 'r').read()
		html = etree.HTML(intext)

		for element in html.iter():
			if (element.tag == "p" and element.text == "News Result"):
				# Do nothing
				pass
	
			elif (element.tag == "a"):
				articleURL = element.attrib["href"]
				articleTitle = element.text

			elif (element.tag == "br"):
				if (element.tail != None):
					summaryText = element.tail

			elif (element.tag == "strong"):
				if (element.tail != "\n"):
					articleSource = element.tail

			elif (element.tag == "p"):
				# Check to see if article already exists using URL. If it exists, don't do anything
				if (articles.find_one({ "url": articleURL }) == None):
				
					# Article will write to a directory created from current filename and code
					articleFileDirectory = path + file + "--files/"
				
					# For each URL, assign a random string as a unique identifier
					code = base64.urlsafe_b64encode(os.urandom(18))
				
					# This code also becomes the filename for the full file path
					articleFilePath = articleFileDirectory + code

					# TODO: Implement article scoring
					score = None
	
					# TODO: Implement dates
					search_date = None
					publish_date = None

					# Download full article and use full-text (if available) for keyword extraction
					fullArticleText = download_article_file(articleURL, articleFileDirectory, code)
			
					if (fullArticleText is not None):
						keyword_set = textrank(fullArticleText) 
					else:
						keyword_set = textrank(summaryText)
					
					keywords = list(keyword_set)

					article = [{
					"q": query,
					"sc": score,
					"c": code,
					"sd": search_date,
					"pd": publish_date,
					"url": articleURL,
					"t": articleTitle,
					"abs": summaryText,
					"sr": articleSource,
					"k": keywords,
					"f": articleFilePath,
					"m": None
					}]
		
					# Write article to MongoDB collection
					article_id = articles.insert(article)
					print "Inserted into articles: " + articleTitle.encode('ascii', 'ignore')



if __name__ == "__main__":
	if len(sys.argv) != 2:
		print "Usage: python article-parse <output-directory>"
		print "Output directory not specified. Will default to /root/search-results/"
		directory = "/root/search-results/"
	else:
		directory = sys.argv[1]	

	# Open MongoDB connection
	connection = MongoClient()
	db = connection.db
	search_terms = db.search_terms

	all_search_terms = search_terms.find_one()
	# TODO: Currently search_terms is one big list. Separate into individual items?
	
	search_terms = all_search_terms['terms']
	
	for term in search_terms:
		# Replace any spaces in term with underscore (_)
		term = term.replace(" ", "_")
	
		# For each keyword in MongoDB, parse the URLs
		try:
			parse_urls(db, directory, term)
		except OSError:
			print "ERROR: Directory for " + term + " doesn't exist! No users had these terms in their profiles?"	

	recommend_articles(db)
