from docket_scraper.spiders.court_connect import CourtConnectCrawlSpider


class CourtConnectDistributedCrawlSpider(CourtConnectCrawlSpider):
    name = 'court-connect-distributed-crawl'
