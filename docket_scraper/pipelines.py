# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from datetime import datetime


class AttachCrawlFieldsPipeline(object):
    def process_item(self, item, spider):
        item = dict(item)
        item['crawler_id'] = spider.crawler_id
        item['spider_name'] = spider.name
        item['crawled_at'] = datetime.utcnow().isoformat()
        return item
