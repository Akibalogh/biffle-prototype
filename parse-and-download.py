import sys

# Add path for textrank
sys.path.append("/root/textrank/")
from textrank import textrank

import os
from os import listdir
from os.path import isfile, join
import traceback
import datetime
from datetime import datetime
import time
import string
import pymongo
from pymongo import MongoClient
#import base64
import hashlib
import lxml.html, lxml.html.clean
from lxml import etree
import urllib2
import httplib
import re
import random
from boilerpipe.extract import Extractor
import simplejson
import StringIO
from dateutil.parser import *
import requests
from functools import wraps
import deliciousapi
import cld
import codecs
import datetime
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta

# Add path for summarize
#sys.path.append("/root/summarize/")
import summarize

import local_passwords
TOPSY_API_KEY = local_passwords.TOPSY_API_KEY
AAFTER_URL = local_passwords.AAFTER_URL
DELICIOUS_USERNAME = local_passwords.DELICIOUS_USERNAME
AAFTER_NEW_API = local_passwords.AAFTER_NEW_API

def guess_date(text):
	buffer = StringIO.StringIO(text)
	for line in buffer.readlines():
        	for match in re.finditer(
	            r"""(?ix)             # case-insensitive, verbose regex
	            \b                    # match a word boundary
        	    (?:                   # match the following three times:
	             (?:                  # either
	              \d+                 # a number,
	              (?:\.|st|nd|rd|th)* # followed by a dot, st, nd, rd, or th (optional)
	              |                   # or a month name
	              (?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)
	             )
	             [\s./-]+             # followed by a date separator or whitespace
	            ){2}                  # do this three times
	            \b                    # and a word boundary
	            (\d){2,4}             # followed by 2, 4 or more digits (i.e. years)
	            \b                    # and end at a word boundary.""",
	            line):
	                #print "%s to %s: %s" % (match.start(), match.end(), match.group(0))

        	        try:
                	        potential_date = match.group(0).lstrip(' ').rstrip(' ')
                       		parsed_date = parse(potential_date)

	                        if (len(potential_date) < 5):
	                                break

	                        if (parsed_date.year < 2000 or parsed_date.year > 2013):
	                                break

	                        #print '\'' + potential_date + '\'       ' + datetime.strftime(parsed_date, 'Read as %m/%d/%Y') + '\n'
				return datetime.strftime(parsed_date, '%Y-%m-%d')

        	        except ValueError:
                	        pass
	return None

class SleepAfter(object):  # pylint: disable-msg=R0903
    """From PRAW: https://github.com/praw-dev/praw/blob/master/praw/decorators.py
    Ensure frequency of API calls doesn't exceed guidelines."""

    def __init__(self, function):
        wraps(function)(self)
        self.function = function
        self.last_call = {}

    def __call__(self, *args, **kwargs):
	api_request_delay = 2
        domain = 'www.reddit.com'
        #config = args[0].config

        if domain in self.last_call:
            last_call = self.last_call[domain]
        else:
            last_call = 0
        now = time.time()
        delay = last_call + api_request_delay - now
        if delay > 0:
            now += delay
            time.sleep(delay)
	    print 'INFO: Sleeping for ' + str(delay) + ' (SleepAfter)'
	self.last_call[domain] = now
        return self.function(*args, **kwargs)

@SleepAfter
def get_article_features(articleText, articleURL):
	features = dict()
	features['technorati_auth_score'] = 0

	# Technorati: Pull in blog authority rating, if available
	for blog_page in tech_blogs.find():
		for blog in blog_page['b']:
			# blog[0] refers to the URL and blog[1] is the Technorati auth score
			if (re.search(blog[0], articleURL) is not None):
				features['technorati_auth_score'] = blog[1]

	# Reddit: See if a corresponding page exists. Use @SleepAfter class to limit Reddit API calls to 1 every 2 seconds
	try:
		reddit_headers = {'User-Agent': "Biffle article recommendations"}
		reddit_url = 'http://www.reddit.com/api/info.json'
		reddit_params = dict(url = articleURL)
		reddit_req = requests.get(reddit_url, params=reddit_params, headers=reddit_headers)
		reddit_children = reddit_req.json['data']['children']
		if (reddit_children == []): # No results were returned
			features['reddit_info'] = None
		else:
			features['reddit_info'] = reddit_children
	
	except simplejson.scanner.JSONDecodeError:
		print "Reddit: unable to find " + articleURL
		features['reddit_info'] = None

	except TypeError:
		#print "ERROR: TypeError at Reddit API"
		features['reddit_info'] = None

	# Twitter: Use the undocumented Twitter API to get the Retweet count (from the Twitter share button)
	try:
		twit_url = 'http://urls.api.twitter.com/1/urls/count.json'
		twit_params = dict(url = articleURL)
		twit_req = requests.get(twit_url, params=twit_params)
		features['retweet_count_all'] = twit_req.json()['count']

	except:
		print "ERROR: Twitter API threw error for " + articleURL
		features['retweet_count_all'] = None
	
	# DISABLED -- Twitter: Use the Topsy API to get the Retweet count (from the Twitter share button)
	#try:
	#	topsy_api_key = TOPSY_API_KEY
	#	topsy_params = dict(url=articleURL, apikey=topsy_api_key)
	#	topsy_url = 'http://otter.topsy.com/stats.json'
	#	topsy_req = requests.get(topsy_url, params=topsy_params)
	#	topsy_json = topsy_req.json
	#	features['retweet_count_all'] = topsy_json['response']['all']
	#	features['retweet_count_influential'] = topsy_json['response']['influential']
	
	#except simplejson.scanner.JSONDecodeError:
	#	print "INFO: Topsy unable to find " + articleURL
	#	features['retweet_count_all'] = None
	#	features['retweet_count_influential'] = None



	# Delicious: Call deliciousapi to get any relevant article data
	try:
		dapi_data = dapi.get_url(articleURL)
		features['delicious_bookmarks'] = dapi_data.bookmarks
		features['delicious_top_tags'] = dapi.top_tags
		features['delicious_tags'] = dapi.tags
	except AttributeError:
		# No attributes found
		#print "INFO: No Delicious attributes found"
		features['delicious_bookmarks'] = None
	except:
		#print "ERROR: Delicious API threw error for " + articleURL
		print "ERROR: Delicious API error ", sys.exc_info()[0]
		features['delicious_bookmarks'] = None

	# Facebook: Use the Facebook Open Graph API to get Facebook share count
        try:
                facebook_params = dict(id=articleURL)
                facebook_url = 'http://graph.facebook.com/'
                facebook_req = requests.get(facebook_url, params=facebook_params)
		features['facebook_shares'] = facebook_req.json()['shares']

        except (simplejson.scanner.JSONDecodeError, KeyError):
                #print "INFO: Facebook unable to find " + articleURL
		features['facebook_shares'] = None

	return features

def map_todays_inserted_domains_from_articles(domain_analysis_outfile):
	re_domain = re.compile("http.*//([^<]*?)/.*") # Match between // and the next /
	domains = {}

	today = datetime.today()
	date_start = datetime.combine(today.date(), time (0, 0, 0, 0))
	date_end = datetime.combine(date(today.year, today.month, today.day + 1), time (0, 0, 0, 0))

        articles_inserted_today = articles.find({ 'procd': { '$gte': date_start, '$lt': date_end }})

	for article in articles_inserted_today:
		domain = re_domain.search(article['url']).group(1)

		if (domains.has_key(domain)):
        		domains[domain] = domains[domain] + 1
	        else:
        		domains[domain] = 1
	
       	# TODO: Figure out if utf-8 is needed or ASCII is OK?
        outfile = codecs.open(domain_analysis_outfile, 'a+', encoding='utf-8')

        # Print tuples to a file
        for key, value in domains.items():
                outfile.write(key + '\t' + str(value) + '\n')

        outfile.close()



def reduce_relevant_domains(domain_analysis_outfile):
        domains = {}

        # Open the workfile and parse domains into a data structure
        infile = codecs.open(domain_analysis_outfile, 'r', encoding='utf-8')

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
        if (os.path.isfile(domain_analysis_outfile)):
                os.unlink(domain_analysis_outfile)
        else:
                raise Exception("ERROR: Can't find domain_analysis_outfile for deletion")

        # Write the data structure to a file
        outfile = codecs.open(domain_analysis_outfile, 'a+', encoding='utf-8')

        for key, value in domains.items():
                outfile.write(key + '\t' + str(value) + '\n')

        outfile.close()



def download_article_file(articleURL, articleFileDirectory, code):
	articleFilePath = articleFileDirectory + code
				
	# Download the article and save as file
	if (articleURL == ""):
		print "ERROR: Empty URL detected! File not created"
		return None
	else:
		# If a directory for files doesn't exist, create it
		dir = os.path.dirname(articleFileDirectory)

		if not os.path.isdir(dir):
			#print "Created directory: " + dir
			os.makedirs(dir)
		
		try:
			#fullArticle = urllib2.urlopen(articleURL)
			#fullArticleText = fullArticle.read()

			# Use boilerpipe to remove boilerplate and formatting
			extractor = Extractor(extractor='ArticleExtractor', url=articleURL)
			fullArticleText = extractor.getText()

			# Test to see if article is in English. If not, then return None
			top_language = cld.detect(fullArticleText.encode('utf-8'))[0]
			if (top_language != 'ENGLISH'):
				print "SKIPPED: Article is in " + top_language
				return None

			outfile = open(articleFilePath, 'w+')			
			outfile.write(fullArticleText.encode('ascii', 'ignore'))
			outfile.close

			# Use lxml's HTML cleaner to remove markup
			#htmltree = lxml.html.fromstring(fullArticleText)		
			#cleaner = lxml.html.clean.Cleaner(remove_unknown_tags=True)
			#cleaned_tree = cleaner.clean_html(htmltree)
			#return cleaned_tree.text_content()
			return fullArticleText
	

		except urllib2.HTTPError:
			print "ERROR: HTTPError. Article file download skipped: " + articleURL	
			return None

		except urllib2.URLError:
			print "ERROR: URLError. Article file download skipped: " + articleURL	
			return None

		except LookupError:
			print "ERROR: LookupError. Article file download skipped: " + articleURL	
			return None
		
		except UnicodeDecodeError:
			print "ERROR: UnicodeDecodeError. Article file download skipped: " + articleURL
			return None

		except:
	                print "ERROR: ", sys.exc_info()[0]
        	        return None

def parse_news_articles(php_directory, download_directory, file_name, query):
	# Note: Assumes that path is stored as <query>.php/
	inpath = php_directory + file_name + "/"
	file_list = [ f for f in listdir(inpath) if isfile(join(inpath,f)) ]

	# For each file, get the article Titles and URLs
	for file in file_list:
		# Clear out any variables from last file
		articleURL = articleTitle = articleSource = summaryText = keywords = score = code = ""
	
		try:	
			intext = open(inpath + file, 'r').read()
			html = etree.HTML(intext)
		except lxml.etree.XMLSyntaxError:
			print "ERROR: XMLSyntaxError when reading " + inpath + file
			break

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
				if (articles.find_one({ "url": articleURL }) is not None):
					print "INFO: Duplicate article found"
				else:
					print "Processing: " + articleURL			
	
					# For each URL, assign its md5 as a unique identifier
					#code = base64.urlsafe_b64encode(os.urandom(18))
					m = hashlib.md5()
					m.update(articleURL)
					code = m.hexdigest()
        				first_level = code[0:2]
					second_level = code[2:4]
					
					# This code also becomes the filename for the full file path
					#articleFileDirectory = php_directory + file + "--news/"
					articleFileDirectory = download_directory + first_level + "/" + second_level + "/"
					articleFilePath = articleFileDirectory + code

					# Download full article and use full-text (if available) for keyword extraction
					fullArticleText = download_article_file(articleURL, articleFileDirectory, code)
			
					if (fullArticleText is not None):
						keyword_set = textrank(fullArticleText) 
						#articleFeatures = get_article_features(fullArticleText, articleURL)
						articleFeatures = None
						guessed_date = guess_date(fullArticleText)
					else:
						keyword_set = textrank(summaryText)
						#articleFeatures = get_article_features(summaryText, articleURL)
						articleFeatures = None
						guessed_date = guess_date(summaryText)
				
					keywords = list(keyword_set)
                        		
					processed_date = datetime.now().strftime("%Y-%m-%d")
					if (guessed_date is not None):
						publish_date = guessed_date
					else:
						publish_date = processed_date
	
					article = [{
					"q": query,
					"c": code,
					"f": articleFeatures,
					"pubd": publish_date,
					"procd": processed_date,
					"url": articleURL,
					"t": articleTitle,
					"abs": summaryText,
					"sr": articleSource,
					"k": keywords,
					"fp": articleFilePath,
					"m": None
					}]
		
                        		# Write article to MongoDB collection
		                        try:
		                                article_id = articles.insert(article)
		                        except MongoException.DuplicateKey:
		                                print "Duplicate key: " + code

		                        #print "Inserted into articles: " + articleTitle.encode('ascii', 'ignore')

					if (fullArticleText is None):
						fullArticleText = summaryText

					# Insert into ElasticSearch	
		                        json_str = mk_es_json(code, fullArticleText, articleURL, articleTitle, summaryText, publish_date)
                		        #print json_str
		                        index = 'article'
              				index_type = 'text'
        		                es_url = 'http://localhost:9200'
                        		r = post_to_elastic_search(es_url, index, index_type, code, json_str)
		                        print r




def parse_webpages(php_directory, term, option, excludes):
	api_base_url = AAFTER_URL
	api_args = "&wt=xml&fl=*,score"
	file_name = (term + '-' + option).replace(" ", "_").replace("/", "_")
	webpageFileDirectory = php_directory + file_name + "--webpages" + "/"
	url_term = urllib2.quote('"' + term + '" ' + option + ' ' + excludes)

	try:
		api_url = api_base_url + url_term + api_args
		#print "Downloading XML from " + api_url
		xml_response = urllib2.urlopen(api_url)

	except urllib2.HTTPError:
		print "ERROR: HTTPError at " + api_url.encode('ascii', 'ignore')
		xml_response = ""

	except urllib2.URLError:
		print "ERROR: URLError at " + api_url.encode('ascii', 'ignore')
		xml_response = ""

	# Parse the XML responses
	xml_tree = etree.parse(xml_response)

	query = xml_tree.xpath("//response/lst[@name='responseHeader']/lst[@name='params']/str[@name='q']/text()")
	num_result = xml_tree.xpath("//response/result")[0].attrib['numFound']

	# Each website result will be stored as a list
	titles = xml_tree.xpath("//response/result/doc/str[@name='name']/text()")
	urls = xml_tree.xpath("//response/result/doc/str[@name='url_s']/text()")
	scores = xml_tree.xpath("//response/result/doc/float[@name='score']/text()")

	# Count the number of urls passed in XML and use that as the basis for how many results are on the page
	url_count = xml_tree.xpath("count(//response/result/doc/str[@name='url_s'])")

	meta_descriptions = meta_keywords = summaries = []

	# Add summary and meta information from Subhankar's API
	# Use loop to avoid IndexError if field does not exist
	for i in range(len(urls)):
		try:
			md = xml_tree.xpath("//response/result/doc/arr[@name='features']/str[1]/text()")[i]
			meta_descriptions.append(md)
		except IndexError:
			meta_descriptions.append("")

		try:
			mk = xml_tree.xpath("//response/result/doc/arr[@name='features']/str[2]/text()")[i]
			meta_keywords.append(mk)
		except IndexError:
			meta_keywords.append("")

		try:
			s = xml_tree.xpath("//response/result/doc/arr[@name='features']/str[3]/text()")[i]
			summaries.append(s)
		except IndexError:
			summaries.append("")
		

	for i in range(len(urls)):
		# Check to see if webpage has already been inserted. If it has, don't do anything
		if (webpages.find_one({ "url": urls[i] }) == None):
			
			fullWebpageText = None
			#code = base64.urlsafe_b64encode(os.urandom(18))
			m = hashlib.md5()
			m.update(urls[i])
			code = m.hexdigest()
			webpageFilePath = webpageFileDirectory + code

			# Download full webpage and use full-text (if available) for keyword extraction
		
			# If a directory for files doesn't exist, create it
			dir = os.path.dirname(webpageFileDirectory)

			if not os.path.isdir(dir):
				#print "Created directory: " + dir
				os.makedirs(dir)
			
			try:	
				#fullWebpage = urllib2.urlopen(urls[i])
				#print "Opening website URL: " + str(urls[i])
				#fullWebpageHTML = fullWebpage.read()


				# Use boilerpipe to clean text
				extractor = Extractor(extractor='ArticleExtractor', url=urls[i])
				#fullWebpageHTML = extractor.getHTML()
				fullWebpageText = extractor.getText()

				# Use lxml's HTML cleaner to remove markup
				#htmltree = lxml.html.fromstring(fullWebpageText)		
				#cleaner = lxml.html.clean.Cleaner(remove_unknown_tags=True)
				#cleaned_tree = cleaner.clean_html(htmltree)
				#fullWebpageText = cleaned_tree.text_content()

				outfile = open(webpageFilePath, 'w+')
				outfile.write(fullWebpageText.encode('ascii', 'ignore'))
				outfile.close

			except urllib2.HTTPError:
				print "HTTPError: Webpage file download skipped: " + urls[i]
				return None

			except urllib2.URLError:
				print "URLError: Webpage file download skipped: " + urls[i]
				return None

			except UnicodeDecodeError:
				print "UnicodeDecodeError: Webpage file download skipped: " + urls[i]
				return None

			except lxml.etree.ParserError:
				print "lxml.etree.ParserError: Webpage file download skipped: " + urls[i]
				return None

			except LookupError:
				print "LookupError: Webpage file download skipped: " + urls[i]
				return None

			if (fullWebpageText is not None):
				keyword_set = textrank(fullWebpageText) 
			else:
				keyword_set = textrank(summaries[i])
		
			keywords = list(keyword_set)
		
			webpage = [{
			"q": query,
			"nr": num_result,
			"url": urls[i],
			"t": titles[i],
			"c": code,
			"md": meta_descriptions[i],
			"mk": meta_keywords[i],
			"abs": summaries[i],
			"s": scores[i],
			"k": keywords,
			"f": webpageFilePath
			}]

			webpage_id = webpages.insert(webpage)
			#print "Inserted into webpages: " + titles[i].encode('ascii', 'ignore')

			# TODO: Insert webpage into ElasticSearch?

def validate_url(url):
	#try:
	#	re_domain = re.compile("http.*//([^<]*?)/(.*)")
	#	domain = re_domain.search(url).group(1)
	#	remainder = re_domain.search(url).group(2)
	#except AttributeError:
	#	print "ERROR: AttributeError. Not a valid URL? (" + url.encode('ascii', 'ignore') + ")"

	try:
		#conn = httplib.HTTPConnection(domain)
		#conn.request('HEAD', remainder)
		#res = conn.getresponse()

		header = requests.head(url)

		# See: http://en.wikipedia.org/wiki/List_of_HTTP_status_codes
		if (header.status_code >= 300):
			print "ERROR: " + str(header.status_code) + " HTTP code returned"
			return False

		# See: http://en.wikipedia.org/wiki/MIME_type#Type_text
		# If the header exists and 'text' is in the header
		if (header.headers['content-type'] and 'text' not in header.headers['content-type']):
			print "SKIPPED: Content-type is not text"
			return False

	except:
		print "ERROR: ", sys.exc_info()[0]
		return False

	return True

def clean_text(text):
    text = text.replace('&rsquo;', "'").replace('&#8217;', "'").replace('\n', '\\n').replace('&amp;', '&').replace('\r','\\r').replace('"','\\"').replace('\t','\\t')
    return text

def mk_es_json(page_id, text, url, title, abst, pd):
    text = clean_text(text)
    title = clean_text(title)
    abst = clean_text(abst)

    json_str = '{'
    json_str += '"text":"'+ text.encode('utf-8') +'"'
    json_str += ',"url":"'+ url.encode('utf-8') + '"'
    if title:
        json_str += ',"title":"'+ title.encode('utf-8') + '"'
    if abst:
        json_str += ',"abst":"'+ abst.encode('utf-8') + '"'
    if pd:
        json_str += ',"date":"'+ pd + '"'
    json_str += '}'
    return json_str

def post_to_elastic_search(es_url, index, index_type, index_id, json_str):
    post_url = es_url+'/'+index+'/'+index_type+'/'+index_id
    try:
        r = requests.post(url=post_url, data=json_str)
    except requests.exceptions.ConnectionError:
        print "connectionError"
    except requests.exceptions.HTTPError:
        print "Http Error"
    except requests.exceptions.RequestException:
        print "request exception"
    else:
        return r.json()

def parse_Subhankar_API_v2(sub_api_v2_path):
	xml_tree = etree.parse('sub_api_v2_path')

	checked_dates = xml_tree.xpath("//documentCollection/documentRecord/checkedDate/text()")
	domains = xml_tree.xpath("//documentCollection/documentRecord/servers/server/text()")
	topics = xml_tree.xpath("//documentCollection/documentRecord/topic[2]/terms[1]/text()")

	for topic in xml_tree.xpath("//documentCollection/documentRecord/topic[2]"):
		# Subtract 1 for <class> tag
		print (len(topic) - 1)
		for term_tag in topic:
			if (term_tag.tag == 'terms'):
				print term_tag.text


	for i in range(len(checked_dates)):
		try:
			pass # TODO: What was here?
		except IndexError:
			print "ERROR: IndexError at: " + str(i)	


def download_articles_from_url(api_url, download_directory):
	# Use the API URL to get a list of articles
	api_req = requests.get(api_url)
	article_list = api_req.text.split('\n')

	# Shuffle the article list to avoid being blocked
	random.shuffle(article_list)
	
	# Creates a Simple Summarizer for summarizing articles
	ss = summarize.SimpleSummarizer()

	for articleURL in article_list:
		if (articles.find_one({ "url": articleURL }) == None):
			#print 'Trying: ' + articleURL.encode('ascii', 'ignore')

			if (validate_url(articleURL) is False):
				continue
		
			# For each URL, assign its md5 as a unique identifier
			m = hashlib.md5()
			m.update(articleURL)
			code = m.hexdigest()
	       		first_level = code[0:2]
			second_level = code[2:4]
					
			# This code also becomes the filename for the full file path
			articleFileDirectory = download_directory + first_level + "/" + second_level + "/"
			articleFilePath = articleFileDirectory + code

			# TODO: Parse title from article

			# Download full article and use full-text (if available) for keyword extraction
			fullArticleText = download_article_file(articleURL, articleFileDirectory, code)
			
			if (fullArticleText is not None):
				keyword_set = textrank(fullArticleText) 
				#articleFeatures = get_article_features(fullArticleText, articleURL)
				articleFeatures = None
				guessed_date = guess_date(fullArticleText)
				summaryText = ss.summarize(fullArticleText,5) # 2nd input is number of lines in summary
			else:
				guessed_date = ""
				# TODO: Fix
				print "ERROR: Full article text not available"
				#keyword_set = textrank(summaryText)
				#articleFeatures = get_article_features(summaryText, articleURL)
				articleFeatures = None
				continue
				
			keywords = list(keyword_set)

			print "Downloaded: " + articleURL.encode('ascii', 'ignore')

			processed_date = datetime.now().strftime("%Y-%m-%d")
			if (guessed_date is not None):
				publish_date = guessed_date
			else:
				publish_date = processed_date			

			article = [{
				#"q": query, # TODO: Fix
				"_id": code,
				"c": code,
				"f": articleFeatures,
				"pubd": publish_date,
				"procd": processed_date,
				"url": articleURL,
				#"t": articleTitle, # TODO: Fix
				"abs": summaryText, # TODO: Fix
				#"sr": articleSource, # TODO: Fix
				"k": keywords,
				"fp": articleFilePath,
				"m": None
				}]
			
			# Write article to MongoDB collection
			try:
				article_id = articles.insert(article)
			except MongoException.DuplicateKey:
				print "Duplicate key: " + code
	
			#print "Inserted into articles: " + articleTitle.encode('ascii', 'ignore')
			title = '' # TODO: Fix
			abstract = '' # TODO: Fix
			json_str = mk_es_json(code, fullArticleText, articleURL, title, abstract, publish_date) 
			#print json_str
			index = 'article'
			index_type = 'text'
			es_url = 'http://localhost:9200'
    			r = post_to_elastic_search(es_url, index, index_type, code, json_str)
			print r
		
	
if __name__ == "__main__":
	php_directory = "/data/search-results/"
	download_directory = "/data/article-files/"
	
	# TODO: Find more excludes
	webpage_excludes = '-meetup.com -buy'

	if len(sys.argv) != 2:
		print "Usage: python parse-and-download.py <output-directory>"
		print "INFO: Output directory not specified. Defaulting to " + php_directory
	else:
		php_directory = sys.argv[1]	

	# Instantiate Delicious API
	dapi = deliciousapi.DeliciousAPI()
	username = DELICIOUS_USERNAME

	# Open MongoDB connection
	connection = MongoClient()
	db = connection.db
	perm = connection.perm
	query_term_options_db = db.queries
	tech_blogs = perm.tech_blogs
	articles = db.articles
	webpages = db.webpages
        cursor = db.all_terms.find({'_id': 1})
        all_terms = cursor[0]['terms']
	
	query_term_options = query_term_options_db.find_one()

	#for qto in query_term_options['q']:
	#	query = qto[0]
	#	term = qto[1]
	#	option = qto[2]
	
	#	# For each keyword and option string, parse the URLs
	#	try:
	#		# Run the parsers by sending the queries (term + option) -- i.e. "MongoDB Healthcare"
	#		print "Parsing: " + term + "-" + option
	#		file_name = (term + "-" + option).replace(" ", "_").replace('/','_')
	#		#parse_webpages(php_directory, term, option, webpage_excludes)
	#		#parse_news_articles(php_directory, download_directory, file_name, query)

	#	except OSError:
	#		print "ERROR: Directory for " + file_name + " doesn't exist! Content wasn't downloaded?"	

	# Subhankar's new article API
	api_url = AAFTER_NEW_API
	now = datetime.now()
	process_date = now.strftime("%Y-%m-%d")
	#download_articles_from_url(api_url, download_directory, process_date)

	# TEST: Using Subhankar's API v1 to download individual terms
	for term in all_terms[0]:
              	try:
                       # Run the parsers by sending the query term -- i.e. "MongoDB"
                       print "Parsing: " + term
                       file_name = term.replace(" ", "_").replace('/','_')
                       #parse_webpages(php_directory, term, option, webpage_excludes)
                       parse_news_articles(php_directory, download_directory, file_name, term)

                except OSError:
                       print "ERROR: Directory for " + file_name + " doesn't exist! Content wasn't downloaded?"




	domain_analysis_outfile = "/root/biffle-prototype/domains_inserted_into_MongoDB"

	# TODO: Over what timeframe should we be analyzing domains? This deletes the file every time
        # Delete previous domain analysis file
        if (os.path.isfile(domain_analysis_outfile)):
                os.unlink(domain_analysis_outfile)
        else:
                print "INFO: Existing domain_analysis_outfile not found for deletion"

	# TODO: Count domains inserted for webpages or downloaded articles from url
	map_todays_inserted_domains_from_articles(domain_analysis_outfile)


	# Print summary statistics
	print "SUMMARY STATISTICS:"
	count_total_articles = articles.find().count()
	print "Total articles: ", count_total_articles

	count_fb_share = articles.find({"f.facebook_shares":{"$exists": True, "$ne": 0}}).count()
	print "Total with Facebook share data: ", count_fb_share, " ({0:.2%})".format(float(count_fb_share)/float(count_total_articles))

	count_retweet_all = articles.find({"f.retweet_count_all":{"$exists": True, "$ne": 0}}).count()
	print "Total retweets: ", count_retweet_all, " ({0:.2%})".format(float(count_retweet_all)/float(count_total_articles))

	#print "Total retweets by influentials: " + str(articles.find({"f.retweet_count_influential":{"$exists": True, "$ne": 0}}).count())

	count_technorati = articles.find({"f.technorati_auth_score":{"$exists": True, "$ne": 0}}).count()
	print "Total with Technorati auth score: ", count_technorati, " ({0:.2%})".format(float(count_technorati)/float(count_total_articles))

	count_publish_date = articles.find({"pubd":{"$exists": True, "$ne": None}}).count()
 	print "Total with publish date (guessed): ", count_publish_date, " ({0:.2%})".format(float(count_publish_date)/float(count_total_articles))

        count_processed_date = articles.find({"procd":{"$exists": True, "$ne": None}}).count()
        print "Total with processed date: ", count_processed_date, " ({0:.2%})".format(float(count_processed_date)/float(count_total_articles))

	count_reddit = articles.find({"f.reddit_info.data.modhash":{"$exists": True, "$ne": None}}).count()
	print "Total that has Reddit data: ", count_reddit, " ({0:.2%})".format(float(count_reddit)/float(count_total_articles))

	count_delicious = articles.find({"f.delicious_bookmarks":{"$exists": True, "$ne": None}}).count()
	print "Total that has Delicious data: ", count_delicious, " ({0:.2%})".format(float(count_delicious)/float(count_total_articles))
