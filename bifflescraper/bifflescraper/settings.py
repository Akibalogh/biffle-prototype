# Scrapy settings for bifflescraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'bifflescraper'
SPIDER_MODULES = ['bifflescraper.spiders']
NEWSPIDER_MODULE = 'bifflescraper.spiders'

LOG_LEVEL = 'INFO'
#LOG_LEVEL = 'WARNING'
LOG_FILE = 'logfile.log'

# See: http://doc.scrapy.org/en/latest/topics/settings.html
# See: http://doc.scrapy.org/en/latest/topics/downloader-middleware.html
COOKIES_ENABLED = False
#DOWNLOAD_DELAY = 0.25
DOWNLOAD_DELAY = 2
#DOWNLOAD_TIMEOUT = 15
ROBOTSTXT_OBEY = True
DOWNLOADER_STATS = True

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'test Scraper www.biffle.co' # Default

# Crawl in BFO order, not DFO order
# See: http://doc.scrapy.org/en/latest/faq.html
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeue.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeue.FifoMemoryQueue'

DOWNLOADER_MIDDLEWARES = {
	'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
	'bifflescraper.middlewares.RotateUserAgentMiddleware': 400,
}

FEED_STORAGE = 'file'
FEED_FORMAT = 'jsonlines'
FEED_URI = '%(time)s.json'

FEED_EXPORTERS = {
#    'json': 'scrapy.contrib.exporter.JsonItemExporter',
    'jsonlines': 'scrapy.contrib.exporter.JsonLinesItemExporter',
    'csv': 'scrapy.contrib.exporter.CsvItemExporter',
#    'xml': 'scrapy.contrib.exporter.XmlItemExporter',
}

FEED_STORAGES = {
    '': 'scrapy.contrib.feedexport.FileFeedStorage',
    'file': 'scrapy.contrib.feedexport.FileFeedStorage',
#    'stdout': 'scrapy.contrib.feedexport.StdoutFeedStorage',
#    's3': 'scrapy.contrib.feedexport.S3FeedStorage',
#    'ftp': 'scrapy.contrib.feedexport.FTPFeedStorage',
}


#SPIDER_MIDDLEWARES = {
#    'bifflescraper.middlewares.ProxyMiddleware': None,
#}

#PROXIES = [{'ip_port': 'us.proxymesh.com:31280', 'akibalogh': 'Generation1234!'},]

