from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
#from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item
from scrapy.http import HtmlResponse
from scrapy import log
from bifflescraper.items import BiffleItem
from boilerpipe.extract import Extractor
from pybloom import BloomFilter
#from pybloom import ScalableBloomFilter


class BiffleSpider(CrawlSpider):
	# See: http://stackoverflow.com/questions/8320730/scrapy-log-handler
	name = 'bifflescraper'

	# Get allowed domains
	#allowed_domains = ['starnewsonline.com']
	allowed_domains = ['www.techcentral.ie']
	#domain_list_path = '/root/semanticgen/domains'
	#allowed_domains = []
	#with open(domain_list_path) as f:
        #	for domain in f:
	#		allowed_domains.append(domain.rstrip('\n'))
	
	#start_urls = ['http://www.starnewsonline.com/']
	start_urls = ['http://www.techcentral.ie']
	#start_urls = []
	#for domain in allowed_domains:
	#	start_urls.append('http://' + domain)

	# Allow all and follow links
	rules = (
		Rule(SgmlLinkExtractor(allow=()), callback='parse_item'),
	)

	# Start the logger
	log.start()

	def parse_item(self, response):
		if not isinstance(response, HtmlResponse):
		    log.msg('Not an HTML file: %s' % response.url, level=log.WARNING)
		    return

		#log.msg('Response from: %s' % response.url, level=log.INFO)
	
		#hxs = HtmlXPathSelector(response)
		#item['id'] = hxs.select('//td[@id="item_id"]/text()').re(r'ID: (\d+)')

		extractor = Extractor(extractor='ArticleExtractor', html=response.body_as_unicode())
	        cleaned_text = extractor.getText()
	
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

		# Eliminate duplicates
		keywordset = set(keywordlist)

		foundlist = []
		# TODO: Return body as ASCII or Unicode?
		for keyword in keywordset:
			if (keyword in cleaned_text): # TODO
				foundlist.append(keyword)

		if (len(foundlist) > 0):
			item = BiffleItem()
			item['url'] = response.url
			item['page'] = cleaned_text
			item['keywords'] = ', '.join(foundlist)
			log.msg("Keyword(s) found: %s" % ', '.join(foundlist), level=log.INFO)
			#yield Request(response.url, callback=self.save_article_file)	
			return item
		else:
			return

	def save_article_file(self, response):
		pass
		#path = self.get_path(response.url)
		#with open(path, 'wb') as f:
		#	f.write(response.body)
