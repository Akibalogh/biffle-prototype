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



def parse_news_articles(db, base_directory, query):
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


def parse_websites(db, term):
	webpages = db.webpages
	api_base_url = "http://www.aafter.org:8983/solr/collection1/select?q="
	api_args = "&wt=xml&fl=*,score"

	try:
		url_term = urllib2.quote(term)
		api_url = api_base_url + url_term + api_args
		xml_response = urllib2.urlopen(api_url)
		#xml_text = xml_response.read()

	except urllib2.HTTPError, urllib2.URLError:
		print "ERROR: Urllib couldn't download XML from API"
	
	# Parse the XML responses
	xml_tree = etree.parse(xml_response)

	query = xml_tree.xpath("//response/lst[@name='responseHeader']/lst[@name='params']/str[@name='q']/text()")
	num_result = xml_tree.xpath("//response/result")[0].attrib['numFound']

	# Each website result will be stored as a list
	titles = xml_tree.xpath("//response/result/doc/str[@name='name']/text()")	
	urls = xml_tree.xpath("//response/result/doc/str[@name='url_s']/text()")
	scores = xml_tree.xpath("//response/result/doc/float[@name='score']/text()")
	versions = xml_tree.xpath("//response/result/doc/long[@name='_version_']/text()")
	#summaries = xml_tree.xpath("//response/result/doc/arr[@name='features']/str[@name='summary']/text()")

	# TODO: Try: Download entire website file?

	for i in range(len(titles)):
		try:

			# Check to see if webpage has already been inserted. If it has, don't do anything
			if (webpages.find_one({ "url": urls[i] }) == None):
				webpage = [{
				"q": query,
				"nr": num_result,
				"url": urls[i],
				"t": titles[i],
				#"abs": summaries[i],
				"s": scores[i],
				"v": versions[i]
				}]

				webpage_id = webpages.insert(webpage)
				print "Inserted into webpages: " + titles[i].encode('ascii', 'ignore')

		except IndexError:
			print "ERROR: Index Error at " + term + " when processing list item " + str(i)
			print "See XML response at: " + api_url


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
		term_without_spaces = term.replace(" ", "_")
	
		# For each keyword in MongoDB, parse the URLs
		try:
			parse_websites(db, term)
			#parse_news_articles(db, directory, term_without_spaces)
		except OSError:
			print "ERROR: Directory for " + term + " doesn't exist! No users had these terms in their profiles?"	
