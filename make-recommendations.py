import sys

# Add path for textrank
sys.path.append("/root/textrank/")
from textrank import textrank

import os
from os.path import isfile, join
import datetime
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
import pymongo
from pymongo import MongoClient
import re
import random
import requests
import codecs
import sendgrid
import operator

import local_passwords
SENDMAIL_EMAIL = local_passwords.SENDMAIL_EMAIL
SENDMAIL_PASS = local_passwords.SENDMAIL_PASS


def map_relevant_domains(term_list, es_url, es_analysis_outfile):
	es_index = 0
	cursor_size = 200
	re_domain = re.compile("http.*//([^<]*?)/.*") # Match between // and the next /
	domains = {}

	# Query ElasticSearch to get the total number of results for this term_list
	term_list_as_query = {'q': '+'.join(term_list), 'search-type': 'count'}

	srch = requests.get(es_url, params=term_list_as_query)
	es_total_hits = srch.json()['hits']['total']

	while (es_index < es_total_hits):
		term_list_as_query = {'q': '+'.join(term_list), 'size': cursor_size, 'from': es_index}
		srch = requests.get(es_url, params=term_list_as_query)

		for hit in srch.json()['hits']['hits']:
			score = hit['_score']
			url = hit['_source']['url']

			# Parse the domain from each URL
			domain = re_domain.search(url).group(1)

			# TODO: Assign a score, based on the ranking and # of total results
			if (domains.has_key(domain)):
				domains[domain] = domains[domain] + 1
			else:
				domains[domain] = 1
	
		es_index += cursor_size

	outfile = codecs.open(es_analysis_outfile, 'a+', encoding='utf-8')
	# Print tuples to a file 
	for key, value in domains.items():
                outfile.write(key + '\t' + str(value) + '\n')

	outfile.close()


def reduce_relevant_domains(es_analysis_outfile):
	domains = {}

	# Open the workfile and parse domains into a data structure
	try:
		infile = codecs.open(es_analysis_outfile, 'r', encoding='utf-8')
	except IOError:
		print "ERROR: es_analysis_outfile not found"
		return

	try: 
		for line in infile.readlines():
			(domain, value) = line.split('\t')	

			if (domains.has_key(domain)):
				domains[domain] = domains[domain] + int(value)
			else:
				domains[domain] = int(value)
	except ValueError:
		print "ERROR: Parse error at " + line
	
	infile.close()

	# Delete the original file
	if (os.path.isfile(es_analysis_outfile)):
		os.unlink(es_analysis_outfile)	
	else:
		raise Exception("ERROR: Can't find es_analysis_outfile for deletion")

	# Sort the data structure by turning it into a list of tuples
	sorted_domains = sorted(domains.iteritems(), key=operator.itemgetter(1))

	# Sort highest to lowest
	sorted_domains.reverse()

	# Pick only the 20 most popular domains
	truncated_domains = sorted_domains[:20]

	# Write the data structure to a file
        outfile = codecs.open(es_analysis_outfile, 'a+', encoding='utf-8')

	#for key, value in domains.items():
	for key, value in truncated_domains:
                outfile.write(key + '\t' + str(value) + '\n')

        outfile.close()

 				
def mk_query_json(terms, date1, date2, size, from_index):
    term_str = ' '.join(terms)
    json_str = '{"query": {' \
                  +  '"filtered": {' \
                  +      '"query" : {' \
                  +          '"text": { "text": "' + term_str +'"}' \
                  +      '},' \
                  +      '"filter": {' \
                  +          '"numeric_range": {' \
                  +              '"date": {' \
                  +                  '"gte": "'+date1+'",' \
                  +                  '"lte": "'+date2+'"' \
                  +              '}' \
                  +          '}' \
                  +      '}' \
                  +  '}' \
                  +  '},' \
                  +  '"size": '+str(size)+',' \
                  +  '"from": '+str(from_index) \
                  +'}' 
    #json_str = '{"query": {"filtered": {"query" : {"text": { "text": "'+term_str+'"}}}},"size": '+str(size)+',"from": '+str(from_index)+'}'
    return json_str


def search(es_url, term_list, date_start, date_end, size, from_index):
    # Add escaped quotes \" \" between search terms
    term_list = ['\\"' + str(s) + '\\"' for s in term_list]
    q = mk_query_json(term_list, date_start, date_end, size, from_index)
    print q
    resp = requests.get(es_url, data=q)
    #print resp.text
    return resp


def recommend_articles_using_es_relevance(db, recommendations_to_make, es_analysis_outfile):
	users = db.users
	articles = db.articles
	recommended_articles = db.recommended_articles_suggested
	recommendations_to_make -= 1 # Recommendations loop is base-0

	# For all users, recommend num_of_recs news articles
	for user in users.find():
		recommendations_made = 0

		print "Making article recommendations for user " + str(user['e'])

		# See if any recommendations were already made today
		today = datetime.today()
                #date_start = datetime.combine(today.date(), time (0, 0, 0, 0))
		# Not used: See if any recommendations made in the last 3 days
		#date_start = today + relativedelta(days =- 3)
                #date_end = datetime.combine(date(today.year, today.month, today.day + 1), time (0, 0, 0, 0))
		date_end = date.today()
		date_delta = timedelta(days=-7)
		date_start = date_end + date_delta
		date_start = str(date_start)
		date_end = str(date_end)
                recommended_articles_in_buffer = recommended_articles.find({ 'uid': user['_id'], 'rt': { '$gte': date_start, '$lt': date_end }})
		recommendations_made += recommended_articles_in_buffer.count()
	
		if (recommended_articles_in_buffer.count() > 0):
			print "INFO: Found " + str(recommended_articles_in_buffer.count()) + " articles in buffer"
			for article in recommended_articles_in_buffer:
				print "Article recommendation already in buffer: ", article['_id']
		else:
			print "INFO: No recommended articles in buffer"

		# Term_list will be used to store the elements in the user's wordcloud
		# Use set() to eliminate duplicates (if any exist)
		term_list = set()

		if (user.has_key('wc')):
			for term in user['wc']:
				term_list.add(term)

		if (len(term_list) == 0):
			print "ERROR: No terms in wordcloud. Moving to next user"
			continue
	
		# Escape '/' character that may cause problem with ElasticSearch
		term_list = [ t.replace('/', '\/') for t in term_list]	
	
		# Initialize ElasticSearch variables
		es_url = 'http://localhost:9200/article/text/_search'
		es_search_size = 50
		es_search_from = 0
		es_result_index = 0

		# Map domains relevant to this user from ES
		map_relevant_domains(term_list, es_url, es_analysis_outfile)

		# Pick articles using ElasticSearch relevance score (and no other criteria)
		while (recommendations_made <= recommendations_to_make):
			
			# Test if we should retrieve the next set of results
			if ((es_result_index % es_search_size) == 0):
			
				# If this is the initial search, don't increment es_search_from
				if (es_result_index is 0):
					pass
				else:
					# If it is, search from next increment
					es_search_from += es_search_size

				# Query ElasticSearch to get topmost results for this term_list
				#term_list_as_query = {'q': '+'.join(term_list), 'size': es_search_size, 'from': es_search_from}
				#srch = requests.get(es_url, params=term_list_as_query)
				srch = search(es_url, term_list, date_start, date_end, es_search_size, es_search_from)
				es_total_hits = srch.json()['hits']['total']
				print "INFO: Querying ElasticSearch. Starting search from ", es_search_from, " out of ", es_total_hits, " total"

			# Test to see if we have more relevant results from the corpus
			if (es_result_index == es_total_hits):
				# No more ElasticSearch results to recommend
				recommendations_made = recommendations_to_make + 1
				continue

			# Return the appropriate result relative to this set of results
			try:
				#print "Returning result ", es_result_index
				chosen_article_id = srch.json()['hits']['hits'][es_result_index % es_search_size]['_id']
			except IndexError:
				# No more hits to recommend within this search
				print "INFO: No more hits to recommend within this search"
				recommendations_made = recommendations_to_make + 1
				continue

			chosen_article = articles.find_one( { "c": chosen_article_id })
			
			if (chosen_article is None):
				print "ERROR: Chosen article not found. ID: " + str(chosen_article_id)
				es_result_index += 1
				continue

			chosen_article_title = chosen_article['t']
			chosen_article_title = chosen_article_title.encode('ascii', 'ignore')

			# Check that articles haven't been sent previously
			if (recommended_articles.find( { "uid": user['_id'], "aid": chosen_article_id } ).count() != 0):
				print "Article already recommended to " + user['e'] + ". Ignore (" + chosen_article_title + ")"
				es_result_index += 1
			else:
				# Put the article in recommended articles
				recommended_article = [{
					"uid": user['_id'],
					"aid": chosen_article_id,
					"rt": datetime.today(),
					"uk": user['k'],
					#"pk": presented_keywords,
				}]

				recommended_article_id = recommended_articles.insert(recommended_article)
				print "Recommended to " + str(user['e']) + " article at index: " + str(es_result_index)

				# Move to the next recommendation
				recommendations_made += 1

				# Move to the next search result
				es_result_index += 1

				#print "Recommendations made: ", recommendations_made, " and Recommendations to make: ", recommendations_to_make

	# Reduce domains and their relevance values
	reduce_relevant_domains(es_analysis_outfile)

def recommend_articles_at_random(db, num_of_recs):
	users = db.users
	articles = db.articles
	recommended_articles = db.recommended_articles_suggested

	# For all users, recommend num_of_recs news articles
	for user in users.find():
		# num_of_recs is base-0
		this_user_num_of_recs = num_of_recs - 1

		print "Making article recommendations for user " + str(user['e'])
		potential_article_matches = []

		# Check to see if there are already any articles to be recommended today
		today = datetime.today()
		date_start = datetime.combine(today.date(), time (0, 0, 0, 0))
		date_end = datetime.combine(date(today.year, today.month, today.day + 1), time (0, 0, 0, 0))
		
		recommended_articles_in_buffer = recommended_articles.find({ 'uid': user['_id'], 'rt': { '$gte': date_start, '$lt': date_end }})
		this_user_num_of_recs -= recommended_articles_in_buffer.count()		
		if (recommended_articles_in_buffer.count() > 0):
			print "INFO: Found " + str(recommended_articles_in_buffer.count()) + " articles in buffer"

		# Find all articles that match the user's keywords
		for keyword in user['k']:
			# Match articles that have been tagged with keyword
			article_matches = articles.find({ "k": { "$regex": re.escape(keyword) } })

			for match in article_matches:
				#print "Potential article match! " + user['e'] + " could get " + str(match['_id'])
				potential_article_matches.append(match['_id'])
		
			print len(potential_article_matches) + " potential matches for user " + user['e']

		# Make max this_user_num_of_recs news recommendations
		recommendations_to_make = min(this_user_num_of_recs, len(potential_article_matches)) 
		recommendations_made = 0

		# Pick articles at random
		while (recommendations_made <= recommendations_to_make):
			if (len(potential_article_matches) == 0):
				#print "No more articles to recommend to " + user['e']
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
				print "Article already recommended to " + user['e'] + ". Ignore (" + chosen_article_title + ")"
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
				print "Recommended to " + str(user['e']) + ": " + chosen_article_title
				recommendations_made += 1


def recommend_webpages(db, num_of_recs):
	users = db.users
	webpages = db.webpages
	recommended_webpages = db.recommended_webpages

	# For all users, recommend num_of_recs webpages
	for user in users.find():
		# Random is base-1 while pop is base-0
		# num_of_recs is base-0
		this_user_num_of_recs = num_of_recs - 1

		potential_webpage_matches = []

		# Check to see if there are already any articles to be recommended today
		today = datetime.today()
		date_start = datetime.combine(today.date(), time (0, 0, 0, 0))
		date_end = datetime.combine(date(today.year, today.month, today.day + 1), time (0, 0, 0, 0))
		
		recommended_webpages_in_buffer = recommended_webpages.find({ 'uid': user['_id'], 'rt': { '$gte': date_start, '$lt': date_end }})
		this_user_num_of_recs -= recommended_webpages_in_buffer.count()	
		if (recommended_webpages_in_buffer.count() > 0):
			print "INFO: Found " + str(recommended_webpages_in_buffer.count()) + " webpages in buffer"

		# Look for matches for webpage recommendations
		for keyword in user['k']:
			# Regex approximate match for string containing keyword -- similar to SQL LIKE
			# TODO: Implement exact match for keyword
			webpage_matches = webpages.find({ "k": { "$regex": ".*" + re.escape(keyword) + ".*" } } )
			for w_match in webpage_matches:
				print "Potential webpage match! " + user['e'] + " could get " + str(w_match['_id'])
				potential_webpage_matches.append(w_match['_id'])

		# Make max this_user_num_of_recs webpage recommendations
		web_recommendations_to_make = min(this_user_num_of_recs, len(potential_webpage_matches))
		web_recommendations_made = 0

		# Pick webpages at random
		while (web_recommendations_made <= web_recommendations_to_make): 
			if (len(potential_webpage_matches) == 0):
				print "No more webpages to recommend to " + user['e']
				web_recommendations_made = (web_recommendations_to_make + 1)
				continue

			# Random is base-1 while pop is base-0
			random_num = random.randrange(1,len(potential_webpage_matches) + 1)
			chosen_webpage_id = potential_webpage_matches.pop(random_num - 1)

			chosen_webpage = webpages.find_one( { "_id": chosen_webpage_id })
			chosen_webpage_title = chosen_webpage['t']
			chosen_webpage_title = chosen_webpage_title.encode('ascii', 'ignore')

			# Check that webpages haven't been sent in the past
			if (recommended_webpages.find( { "uid": user['_id'], "wid": chosen_webpage_id } ).count() != 0):
				print "Webpage was recommended to " + user['e'] + " in the past. Ignore (" + chosen_webpage_title + ")"
				pass
			else:
				# Put the webpage in recommended webpages
				recommended_webpage = [{
					"uid": user['_id'],
					"wid": chosen_webpage_id,
					"rt": datetime.today(),
					"uk": user['k'],
					}]

				recommended_webpage_id = recommended_webpages.insert(recommended_webpage)
				print "Recommended to " + str(user['e']) + ": " + chosen_webpage_title
				web_recommendations_made += 1

def senddomainfile(dumpfilename, fulldumpfilepath):
	tempoutfilename = 'senddomain_temp'
	tempoutfilepath = os.path.join(os.getcwd(), tempoutfilename)

        if (os.path.isfile(fulldumpfilepath)):
		# Open file, remove values, and write as a temp file
		infile = open(fulldumpfilepath, 'r')
		tempoutfile = open(tempoutfilename, 'w')
		for line in infile.readlines():
			tempoutfile.write(line.split('\t')[0] + '\n')
		infile.close()
		tempoutfile.close()

	        s = sendgrid.Sendgrid(SENDMAIL_EMAIL, SENDMAIL_PASS, secure=True)
	        message = sendgrid.Message(SENDMAIL_EMAIL, "Today's Biffle Keywords",
	                "plaintext message body", "Today's domains in the attachment")

                message.add_attachment(dumpfilename, tempoutfilepath)
        else:
                print "ERROR: Attachment not found", tempoutfilepath
		return

        message.add_to(SENDMAIL_EMAIL) # CC: on everything for testing purposes

        # use the Web API to send your message
        s.web.send(message)
        # use the SMTP API to send your message
        #s.smtp.send(message)



if __name__ == "__main__":
	# Open MongoDB connection
	connection = MongoClient()
	db = connection.db

	# Determine which domains produced relevant articles
	#domain_analysis_outfile = 'domains_relevant_from_ES'
	domain_analysis_outfile = "link_" + str(date.today().strftime('%Y_%m_%d')) + ".txt"
	fulldumpfilepath = "/root/biffle-prototype/sub_api/" + domain_analysis_outfile

	# Delete previous domain analysis file
	if (os.path.isfile(fulldumpfilepath)):
        	os.unlink(fulldumpfilepath)
	else:
        	print "INFO: Existing domain_analysis_outfile not found for deletion"
        #	#raise Exception("ERROR: Can't find es_analysis_outfile for deletion")

	# Make 20 article and website recommendations
	recommend_articles_using_es_relevance(db,15, fulldumpfilepath)
	#recommend_articles_at_random(db,4, domain_analysis_outfile)
	#recommend_webpages(db,4, domain_analysis_outfile)

	# Send domain email file
	senddomainfile(domain_analysis_outfile, fulldumpfilepath)	
