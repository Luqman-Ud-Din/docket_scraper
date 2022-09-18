# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from datetime import datetime

import pymongo


class AttachCrawlFieldsPipeline(object):
    def process_item(self, item, spider):
        item = dict(item)
        item['crawling_job_id'] = spider.crawling_job_id
        item['crawler_id'] = spider.crawler_id
        item['spider_name'] = spider.name
        item['crawled_at'] = datetime.utcnow().isoformat()
        return item


class MongoDBPipeline:

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[f'job-{spider.crawling_job_id}'].insert_one(dict(item))
        return item
