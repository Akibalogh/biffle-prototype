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

	# Adjust by 1 since for loop is base-0
	for pageNum in range(1,maxPage + 1):
		# Check to see whether Mongo already has this data. If it does, then continue to the next
		if (tech_blogs.find({ '_id': pageNum }).count() != 0):
			print "Skipping Page: " + str(pageNum)
			continue

		newUrls = getBlogUrls(BASE_URL + SECTION + APPEND + str(pageNum))
		urlCounter += len(newUrls)
		print "Page: " + str(pageNum) + "  Added: " + str(len(newUrls)) + " Total: " + str(urlCounter)

		# Check to see if the record already exists. If not, insert it
		if (tech_blogs.find({ '_id': pageNum }).count() == 0):
			# Upsert URLs into a record
			ret = tech_blogs.update({'_id': pageNum},
				{'$push': {'u': newUrls}},
				True )

except (urllib2.HTTPError, urllib2.URLError):
	print "ERROR: Couldn't download " + BASE_URL + SECTION + pageNum 

except UnicodeDecodeError:
	print "ERROR: Couldn't decode " + BASE_URL + SECTION + pageNum
