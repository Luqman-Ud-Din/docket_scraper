import uuid

from scrapy import Spider
from scrapy_redis.spiders import RedisCrawlSpider


class BaseParseSpider(Spider):
    name = 'base-parse'

    def parse(self, response, **kwargs):
        raise NotImplementedError

    def parse_id(self, response):
        raise NotImplementedError


class BaseCrawlSpider(RedisCrawlSpider):
    name = 'base-crawl'
    parse_spider = BaseParseSpider()

    def __init__(self, crawling_job_id=None, *args, **kwargs):
        super(BaseCrawlSpider, self).__init__(*args, **kwargs)

        if not crawling_job_id:
            raise AttributeError('"crawling_job_id" is a required parameter.')

        self.crawling_job_id = crawling_job_id
        self.crawler_id = str(uuid.uuid4())
        self.seen_item_ids = set()

    def parse(self, response, **kwargs):
        yield from self._parse_response(response, None, {})

    def parse_item_id(self, response):
        return self.parse_spider.parse_id(response)

    def parse_item(self, response):
        item_id = self.parse_item_id(response)
        if self.is_seen_item(item_id):
            return

        return self.parse_spider.parse(response)

    def is_seen_item(self, item_id):
        if item_id in self.seen_item_ids:
            return True

        self.seen_item_ids.add(item_id)
