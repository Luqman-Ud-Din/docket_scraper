import uuid
from datetime import datetime

from scrapy import Spider
from scrapy.spiders import CrawlSpider


class SpiderInitializerMixin:
    def initialize_spider(self):
        self.crawl_id = str(uuid.uuid4())
        self.crawl_start_time = datetime.utcnow().isoformat()
        self.seen_item_ids = set()


class BaseParseSpider(SpiderInitializerMixin, Spider):
    name = 'base-parse'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BaseParseSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.initialize_spider()
        return spider

    def parse(self, response, **kwargs):
        raise NotImplementedError

    def parse_id(self, response):
        raise NotImplementedError


class BaseCrawlSpider(SpiderInitializerMixin, CrawlSpider):
    name = 'base-crawl'
    parse_spider = BaseParseSpider()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BaseCrawlSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.initialize_spider()
        return spider

    def parse(self, response, **kwargs):
        for request_or_item in self._parse_response(response, None, {}):
            yield request_or_item

    def parse_item(self, response):
        item_id = self.parse_spider.parse_id(response)
        if self.is_seen_item(item_id):
            return

        return self.parse_spider.parse(response)

    def is_seen_item(self, item_id):
        if item_id in self.seen_item_ids:
            return True

        self.seen_item_ids.add(item_id)
