from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item
from scrapy.http import HtmlResponse
from scrapy.http.request import Request
from scrapy import log
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from bifflescraper.items import BiffleItem
from boilerpipe.extract import Extractor
from pybloom import BloomFilter
#from pybloom import ScalableBloomFilter
from datetime import datetime
import urlparse
import re
import os
from os.path import isfile, join
import codecs

class BiffleSpider(CrawlSpider):
	# See: http://stackoverflow.com/questions/8320730/scrapy-log-handler
	name = 'bifflescraper'
	
	# Use a Bloom Filter to track what URLs have already been visited
	# See: https://github.com/jaybaird/python-bloomfilter
	global url_bf
	url_bf = BloomFilter(capacity=100000, error_rate=0.01)

	#allowed_domains = ['starnewsonline.com']
	#start_urls = ['http://www.starnewsonline.com/']

	allowed_domains = ['www.techcentral.ie']
	start_urls = ['http://www.techcentral.ie']

	# Get allowed domains
	#domain_list_path = '/root/semanticgen/domains'
	#allowed_domains = []
	#with open(domain_list_path) as f:
        #	for domain in f:
	#		allowed_domains.append(domain.rstrip('\n'))
	#start_urls = []
	#for domain in allowed_domains:
	#	start_urls.append('http://' + domain)

	# Allow all and follow links
	rules = (
		Rule(SgmlLinkExtractor(allow=()), callback='parse_page', follow=True),
	)

	# Start the logger
	log.start()
	
	def __init__(self, *a, **kw):
        	super(BiffleSpider, self).__init__(*a, **kw)
		dispatcher.connect(self.reduce_at_finish, signals.spider_closed)

	def map_keyword_count(self, found_list):
		filename = '/root/biffle-prototype/bifflescraper/keyword_map'
		with open(filename, 'a') as f:
			for keyword in found_list:
				f.write(keyword + ' 1\n')

	def reduce_at_finish(self):
		keywords = {}
		filename = '/root/biffle-prototype/bifflescraper/keyword_map'		

		# Open the workfile and parse domains into a data structure
		# TODO: Is utf-8 needed?
		infile = codecs.open(filename, 'r', encoding='utf-8')

		try:
			for line in infile.readlines():
				(keyword, value) = line.split(' ')

				if (keywords.has_key(keyword)):
					keywords[keyword] = keywords[keyword] + int(value)
				else:
					keywords[keyword] = int(value)
		except ValueError:
			log.msg("Parse error at %s" % line, level=log.ERROR)

		infile.close()

		# Delete the original file
		if (os.path.isfile(filename)):
			os.unlink(filename)
		else:
			raise Exception("ERROR: Can't find keyword file for deletion")

		# Write the data structure to a file
		outfile = codecs.open(filename, 'a+', encoding='utf-8')
		for key, value in keywords.items():
				outfile.write(key + ' ' + str(value) + '\n')
		outfile.close()


	#                              Set search depth here
	def parse_page(self, response, depth=2):
		if not isinstance(response, HtmlResponse):
		    log.msg('Not an HTML file: %s' % response.url, level=log.WARNING)
		    return

		log.msg('Response from: %s' % response.url, level=log.INFO)
		url_bf.add(response.url)
	
		# TODO: Shift this into class __init__ code?
		keywordfilepath = '/root/biffle-prototype/utils/1gram-keyword-dump'
		keywordlist = []
		with open(keywordfilepath) as f:
		        for keyword in f:
				# TODO: Figure out a better way to implement. Here, filter 2-letter keywords.
				if (len(keyword) > 2):
					keywordlist.append(keyword.rstrip('\n'))

		# TODO: Extract page title
	
		extractor = Extractor(extractor='ArticleExtractor', html=response.body_as_unicode())
		cleaned_text = extractor.getText()

		# Eliminate duplicates
		keywordset = set(keywordlist)

		found_list = []
		for keyword in keywordset: # TODO: Is there a more efficient way to do this?
			# Look at word boundaries to match entire words only
			if (re.search(r'\b' + re.escape(keyword) + r'\b', cleaned_text)):
				found_list.append(keyword)

		# Parse this page		
		item = BiffleItem()
		if (len(found_list) > 0):
			item['url'] = response.url
			item['body'] = cleaned_text
			item['keywords'] = ', '.join(found_list)
			item['process_date'] = datetime.today()
			log.msg("Keyword(s) found: %s" % ', '.join(found_list), level=log.INFO)
			self.map_keyword_count(found_list)
			yield item

		if (depth > 0):	
			# Find the next requests and yield those
			hxs = HtmlXPathSelector(response)
			links = hxs.select('//a/@href').extract()
			log.msg('Links on page: %s' % len(links), level=log.INFO)
			for l in links:
				l = urlparse.urljoin(response.url, l)
				if (l not in url_bf):
					url_bf.add(l)
					#log.msg('Found link: %s | From URL: %s' % (l, response.url), level=log.INFO)
					# Decrement depth for next layer of links
					callback = lambda response: self.parse_page(response, depth=(depth - 1))
					yield Request(l, callback=callback)

