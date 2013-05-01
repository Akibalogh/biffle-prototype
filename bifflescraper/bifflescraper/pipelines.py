#from boilerpipe.extract import Extractor

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

class BifflePipeline(object):
    def process_item(self, item, spider):
	#extractor = Extractor(extractor='ArticleExtractor', html=item['page'])
        #item['page'] = extractor.getText()
        return item
