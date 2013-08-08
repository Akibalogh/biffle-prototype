import datetime
from datetime import datetime, date, time, timedelta
import string
import pymongo
from pymongo import MongoClient
import sendgrid
import urllib
import urllib2
import simplejson as json
import requests
import sys
import os

import local_passwords
SENDMAIL_EMAIL = local_passwords.SENDMAIL_EMAIL
SENDMAIL_PASS = local_passwords.SENDMAIL_PASS
LAUNCHBIT_API_KEY = local_passwords.LAUNCHBIT_API_KEY
BIFFLE_REDIRECT_URL = local_passwords.BIFFLE_REDIRECT_URL

def sendemail(recipient, body):
	# make a secure connection to SendGrid
	s = sendgrid.Sendgrid(SENDMAIL_EMAIL, SENDMAIL_PASS, secure=True)

	# make a message object
	message = sendgrid.Message(SENDMAIL_EMAIL, "Today's Biffle Recommendations", 
		"plaintext message body", body)

	# add a recipient
	#message.add_to(recipient)
	message.add_to(SENDMAIL_EMAIL) # CC: on everything for testing purposes

	# use the Web API to send your message
	s.web.send(message)

	# use the SMTP API to send your message
	#s.smtp.send(message)


def senderror(recipient, errormessages):
	s = sendgrid.Sendgrid(SENDMAIL_EMAIL, SENDMAIL_PASS, secure=True)
	message = sendgrid.Message(SENDMAIL_EMAIL, "Biffle Error Message", 
		"plaintext message body", errormessages)
	message.add_to(recipient)
	s.web.send(message)
	#s.smtp.send(message)

def build_email(body, api_key, user_id):
	topfile = open('/root/biffle-prototype/email-templates/coffee-top', 'r')
	top = topfile.read()

	# Pull text ad from LaunchBit API v1.0
	adurl = 'http://www.launchbit.com/api/v1.0/' + api_key + '/adunit/test/9/'
	try:
		adObject = urllib2.urlopen(adurl)
		adDict = json.load(adObject)		
		ad = '<br><br>'
		#ad += '<a href="' + adDict['ad_url'] + '">' + adDict['ad_title'] + '</a><br>'
                # TODO: Pass URL to listener servlet
		url_string = url_listener_url + '?code=' + adDict['ad_url'] + '&content=d' + '&uid=' + str(user_id)
                ad += '<a href="' + url_string + '">' + adDict['ad_title'] + '</a><br>'
		ad += adDict['ad_body'] + '<img src="' + adDict['pixel'] + '">'
	
	except urllib2.URLError:
		print "ERROR: URLError when retrieving LaunchBit ad"
		ad = ''

	except urllib2.HTTPError:
		print "ERROR: HTTPError when retrieving LaunchBit ad"
		ad = ''

	bottomfile = open('/root/biffle-prototype/email-templates/coffee-bottom', 'r')
	bottom = bottomfile.read()

	return top + body + ad + bottom


def email_recommendations():
	for user in users.find():
		body = ""
		#body = "<b>Biffle recommends you check out:</b><br><br>"
		email = user['e']

                # See if any recommendations were made today
                today = datetime.today()
                date_start = datetime.combine(today.date(), time (0, 0, 0, 0))
                # Not used: See if any recommendations made in the last 3 days
                #date_start = today + relativedelta(days =- 3)
                date_end = datetime.combine(date(today.year, today.month, today.day + 1), time (0, 0, 0, 0))
		
		# Find news articles recommended today and send them
                recommended_articles_today = recommended_articles.find({ 'uid': user['_id'], 'rt': { '$gte': date_start, '$lt': date_end }})

		#body += 'Keywords from your social media profiles: '
		#for keyword in user['k']:
		#	body += keyword + ' '

		#body += "<br><br><b>Recommended News Articles:</b><br><br>"
		
		if (recommended_articles_today.count() == 0):
			print "ERROR: No new article recommendations"
			errormessages += "ERROR: No new article recommendations for user: " + email + "<br>"
			#body += "No new article recommendations today!"
			continue

		# Pull recommended articles and put in body
		for recommended_article in recommended_articles_today:	
			article_id = recommended_article['aid']
			match_articles = articles.find({ 'c': article_id })

			for article_match in match_articles:
				#body += '<a href="' + article_match['url'] + '">' + article_match['t'] + '</a><br>'
				# Pass encoded URLs to listener servlet
				url_string = url_listener_url + '?code=' + article_match['c'] + '&content=a' + '&uid=' + str(user['_id'])
				body += '<a href="' + url_string + '">' + article_match['t'] + '</a><br><br>'

				#body += '<br>DEBUG ONLY -- Keywords from article: '
				#for article_keyword in article_match['k']:
				#	body += '[' + article_keyword.encode('ascii', 'ignore') + '] '


		# TODO: Implement webpage recommendations
		#body += "<br><br><b>Recommended webpages:</b><br><br>"
		#
		# Find recommended webpages and send them
		#recommended_webpages_today = recommended_webpages.find({ 'uid': user['_id'] })
		#
		#if (recommended_webpages_today.count() == 0):
		#	body += "No new webpage recommendations today!"

		# Pull recommended articles and put in body
		#for recommended_webpage in recommended_webpages_today:
		#	webpage_id = recommended_webpage['wid']
		#	# TODO: Should be matching 'c' or '_id'?
		#	match_webpages = webpages.find({ '_id': webpage_id })
		
		#	for webpage_match in match_webpages:
		#		#body += '<a href="' + webpage_match['url'] + '">' + webpage_match['t'] + '</a><br>'
		#		# Pass encoded URLs to listener servlet
		#		url_string = url_listener_url + '?code=' + webpage_match['c'] + '&content=w' + '&uid=' + str(user['_id'])
		#		body += '<a href="' + url_string + '">' + webpage_match['t'] + '</a><br><br>'

		print "Emailed " + str(recommended_articles_today.count()) + " news articles to " + email
		body = build_email(body, launchbit_api_key, user['_id'])
		sendemail(email, body)

	# If there are any error messages, send them
	if (errormessages is not ""):
		senderror(SENDMAIL_EMAIL, errormessages)


def curation_email_and_file(outfilepath):
	# Delete previous curation file
	if (os.path.isfile(outfilepath)):
		os.unlink(outfilepath)

	outfile = open(outfilepath, 'a')

	errormessages = ""
	for user in users.find():
		#body = ""
		body = "<b>Curation request for:</b>" + user['e'] + "<br><br>"

                # See if any recommendations were made today
                today = datetime.today()
                date_start = datetime.combine(today.date(), time (0, 0, 0, 0))
                # Not used: See if any recommendations made in the last 3 days
                #date_start = today + relativedelta(days =- 3)
                date_end = datetime.combine(date(today.year, today.month, today.day + 1), time (0, 0, 0, 0))
		
		# Find news articles recommended today and send them
                recommended_articles_today = recommended_articles.find({ 'uid': user['_id'], 'rt': { '$gte': date_start, '$lt': date_end }})

		if (recommended_articles_today.count() == 0):
			print "ERROR: No new article recommendations"
			errormessages += "ERROR: No new article recommendations for user: " + user['e'] + "<br>"
			#body += "No new article recommendations today!"
			continue

		# Pull recommended articles and put in body
		for recommended_article in recommended_articles_today:	
			article_id = recommended_article['aid']
			match_articles = articles.find({ 'c': article_id })

			for article_match in match_articles:
				body += '<a href="' + article_match['url'] + '">' + article_match['t'] + '</a><br>'
				outfile.write('{0}\t{1}\t{2}\n'.format(str(0), user['e'], article_match['url']))

		print "Sent " + str(recommended_articles_today.count()) + " news articles for curation. Email: " + user['e']
	
		# Send via SendGrid
		# make a secure connection to SendGrid
		s = sendgrid.Sendgrid(SENDMAIL_EMAIL, SENDMAIL_PASS, secure=True)
		message = sendgrid.Message(SENDMAIL_EMAIL, "Curation Request", 
		"plaintext message body", body)
		message.add_to(SENDMAIL_EMAIL)
		s.web.send(message)
		#s.smtp.send(message)

	# If there are any error messages, send them
	if (errormessages is not ""):
		senderror(SENDMAIL_EMAIL, errormessages)

	outfile.close()


def import_curated_and_send(infilepath):
	infile = open(infilepath, 'r')
	articles_to_send = {}

	for line in infile.readlines():
		value, email, url = line.rstrip('\n').split('\t')
		if (int(value) == 1):
			if (articles_to_send.has_key(email)):
				articles_to_send[email] += [url]
			else:
				articles_to_send[email] = [url]

	for user in users.find():
		body = ""

                if ((not articles_to_send.has_key(user['e'])) or (len(articles_to_send[user['e']]) == 0)):        
			print "INFO: No new article recommendations for user", user['e']
                        #errormessages += "ERROR: No new article recommendations for user: " + email + "<br>"
                        #body += "No new article recommendations today!"
                        continue

                # Pull recommended articles and put in body
                for article_url in articles_to_send[user['e']]:
			article_match = articles.find_one({'url': article_url})
                        #body += '<a href="' + article_match['url'] + '">' + article_match['t'] + '</a><br>'
                        # Pass encoded URLs to listener servlet
                        url_string = url_listener_url + '?code=' + article_match['c'] + '&content=a' + '&uid=' + str(user['_id'])
                        body += '<a href="' + url_string + '">' + article_match['t'] + '</a><br><br>'

		print "Emailed " + str(len(articles_to_send[user['e']])) + " news articles to " + email
                body = build_email(body, launchbit_api_key, user['_id'])
                sendemail(email, body)



if __name__ == "__main__":
	# Open MongoDB connection
	connection = MongoClient()
	db = connection.db
	users = db.users
	articles = db.articles
	webpages = db.webpages
	recommended_articles = db.recommended_articles_suggested
	recommended_articles_sent = db.recommended_articles_sent
	recommended_webpages = db.recommended_webpages
	launchbit_api_key = LAUNCHBIT_API_KEY
	url_listener_url = BIFFLE_REDIRECT_URL
	
	try:
		argument = sys.argv[1].rstrip()
	except:
		print "Usage: python send-recommendations.py (export|import)"
		sys.exit(1)

	if (argument == 'export'):
		#print "Exporting for curation"
		curation_email_and_file('curation_export')
	elif (argument == 'import'):
		#print 'Importing to send to users'
		import_curated_and_send('curation_export')
		# Delete file? os.unlink('curation_export')
	else:
		print "Usage: python send-recommendations.py (export|import)"
		sys.exit(1)
