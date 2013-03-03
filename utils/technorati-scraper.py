import urllib2
from bs4 import BeautifulSoup
import re
import pymongo
from pymongo import MongoClient

BASE_URL = 'http://technorati.com'
SECTION = '/blogs/directory/technology'
APPEND = '/page-'
maxPage = 0
pageNum = 1
urlCounter = 0

# Initialize MongoDB
connection = MongoClient()
db = connection.db
tech_blogs = db.tech_blogs


def getBlogUrls(pageUrl):
	site = urllib2.urlopen(pageUrl)
	siteHTML = BeautifulSoup(site.read().decode('utf-8'))
	siteLinks = []

	for table in siteHTML.find_all('td', class_='site-details'):
		links = table.find_all("a", class_="offsite")

		for link in links:
			siteLinks.append(link['href'])

	return siteLinks




try:
	baseSite = urllib2.urlopen(BASE_URL + SECTION)
	baseHTML = BeautifulSoup(baseSite.read().decode('utf-8'))

except (urllib2.HTTPError, urllib2.URLError):
	print "ERROR: Couldn't download " + BASE_URL + SECTION

except UnicodeDecodeError:
	print "ERROR: Couldn't decode " + BASE_URL + SECTION



try: 
	for link in baseHTML.find_all(href=re.compile(SECTION + APPEND)):
		maxPage = max(int(link.get('href')[33:].rstrip('/')), maxPage)

	# Get URLs from the first page
	newUrls = getBlogUrls(BASE_URL + SECTION)
	urlCounter += len(newUrls)
	# pageNum is set to 1 at start
	print "Page: " + str(pageNum) + "  Added: " + str(len(newUrls)) + " Total: " + str(urlList)

	# Upsert is set to True so that if the record doesn't exist, it gets created
	ret = all_terms.update({'_id': pageNum},
		{'$push': {'u': newUrls}},
		True ) 

	# Skip page 1 as we've already pulled it
	for pageNum in range(2,maxPage + 1):
		newUrls = getBlogUrls(BASE_URL + SECTION + APPEND + str(pageNum))
		urlCounter += len(newUrls)
		print "Page: " + str(pageNum) + "  Added: " + str(len(newUrls)) + " Total: " + str(urlList)

		# Add terms into record 1. Upsert is set to True
		ret = all_terms.update({'_id': pageNum},
			{'$push': {'u': newUrls}},

except (urllib2.HTTPError, urllib2.URLError):
	print "ERROR: Couldn't download " + BASE_URL + SECTION + pageNum 

except UnicodeDecodeError:
	print "ERROR: Couldn't decode " + BASE_URL + SECTION + pageNum
