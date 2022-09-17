# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface


class AttachCrawlFieldsPipeline(object):
    def process_item(self, item, spider):
        item = dict(item)
        item['crawl_id'] = spider.crawl_id
        item['spider_name'] = spider.name
        item['crawl_start_time'] = spider.crawl_start_time
        return item
