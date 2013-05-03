from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item
from scrapy.http import HtmlResponse
from scrapy.http.request import Request
from scrapy import log
from bifflescraper.items import BiffleItem
from boilerpipe.extract import Extractor
from pybloom import BloomFilter
#from pybloom import ScalableBloomFilter
from datetime import datetime
import urlparse
import re

class BiffleSpider(CrawlSpider):
	# See: http://stackoverflow.com/questions/8320730/scrapy-log-handler
	name = 'bifflescraper'

	allowed_domains = ['starnewsonline.com']
	start_urls = ['http://www.starnewsonline.com/']

	#allowed_domains = ['www.techcentral.ie']
	#start_urls = ['http://www.techcentral.ie']

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

	def parse_page(self, response, recursion=True):
		if not isinstance(response, HtmlResponse):
		    log.msg('Not an HTML file: %s' % response.url, level=log.WARNING)
		    return

		log.msg('Response from: %s' % response.url, level=log.INFO)
	
		# TODO: Shift this into class __init__ code
		keywordfilepath = '/root/biffle-prototype/utils/1gram-keyword-dump'
		# See: https://github.com/jaybaird/python-bloomfilter
		#keywordbf = BloomFilter(capacity=100000, error_rate=0.01)
		keywordlist = []
		with open(keywordfilepath) as f:
		        for keyword in f:
		                #keywordbf.add(keyword.rstrip())
				# TODO: Figure out a better way to implement. Here, filter 2-letter keywords.
				if (len(keyword) > 2):
					keywordlist.append(keyword.rstrip('\n'))
	
		extractor = Extractor(extractor='ArticleExtractor', html=response.body_as_unicode())
		cleaned_text = extractor.getText()

		# Eliminate duplicates
		keywordset = set(keywordlist)

		foundlist = []
		for keyword in keywordset: # TODO: Is there a more efficient way to do this?
			# Look at word boundaries to match entire words only
			if (re.search(r'\b' + re.escape(keyword) + r'\b', cleaned_text)):
				foundlist.append(keyword)

		# Parse this page		
		item = BiffleItem()
		if (len(foundlist) > 0):
			item['url'] = response.url
			item['body'] = cleaned_text
			item['keywords'] = ', '.join(foundlist)
			item['process_date'] = datetime.today()
			log.msg("Keyword(s) found: %s" % ', '.join(foundlist), level=log.INFO)
			yield item

		if (recursion is True):	
			# Find the next requests and yield those
			hxs = HtmlXPathSelector(response)
			links = hxs.select('//a/@href').extract()
			log.msg('Links on page: %s' % len(links), level=log.INFO)
			for l in links:
				l = urlparse.urljoin(response.url, l)
				#log.msg('link: %s' % l, level=log.INFO)

				# Recursion is set to false so further links aren't followed
				# See: https://groups.google.com/forum/?fromgroups=#!topic/scrapy-users/zwrQYp3mguk
				callback = lambda response: self.parse_page(response, recursion=False)
				yield Request(l, callback=callback)


	def save_article_file(self, response):
		pass
		#path = self.get_path(response.url)
		#with open(path, 'wb') as f:
		#	f.write(response.body)
