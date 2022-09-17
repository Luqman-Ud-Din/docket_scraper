# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from random_user_agent.params import SoftwareName, HardwareType, Popularity
from random_user_agent.user_agent import UserAgent
from scrapy import signals


# useful for handling different item types with a single interface


class DocketScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class DocketScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomUserAgentMiddleware(object):
    useragent_limit = 100
    fixed_user_agent_onstart = False

    useragent_browsers = [
        SoftwareName.FIREFOX.value, SoftwareName.CHROME.value, SoftwareName.SAFARI.value
    ]
    useragent_hardware = [
        HardwareType.COMPUTER.value
    ]
    useragent_popularity = [
        Popularity.POPULAR.value
    ]

    def __init__(self, browsers=[], hardwares=[], popularity=[], limit=None):
        self.user_agent_rotator = UserAgent(software_names=browsers, hardware_types=hardwares,
                                            popularity=popularity, limit=limit)

    @classmethod
    def from_crawler(cls, crawler):
        browsers = getattr(crawler.spider, "useragent_browsers", cls.useragent_browsers)
        hardwares = getattr(crawler.spider, "useragent_hardware", cls.useragent_hardware)
        popularity = getattr(crawler.spider, "useragent_popularity", cls.useragent_popularity)
        limit = getattr(crawler.spider, "useragent_limit", cls.useragent_limit)
        fixed_on_start = getattr(crawler.spider, 'fixed_user_agent_onstart', cls.fixed_user_agent_onstart)

        user_agent_middleware = cls(browsers=browsers, hardwares=hardwares, popularity=popularity, limit=limit)
        user_agent_middleware.log_configurations(crawler.spider, browsers, hardwares, popularity, limit, fixed_on_start)

        return user_agent_middleware

    def log_configurations(self, spider, browsers, hardware, popularity, limit, fixed_on_start):
        user_agents = [ua["user_agent"] for ua in self.user_agent_rotator.get_user_agents()]
        spider.log(f"List of User Agents = {user_agents}")
        spider.log(f"useragent_browsers: {browsers}")
        spider.log(f"useragent_hardware: {hardware}")
        spider.log(f"useragent_popularity: {popularity}")
        spider.log(f"useragent_limit: {limit}")
        spider.log(f"fixed_user_agent_onstart: {fixed_on_start}")

    def get_specific_spider_user_agent(self, spider):
        user_agent_attr = getattr(spider, "user_agent", None)
        if user_agent_attr:
            return user_agent_attr

        # But wait, it might also be in the custom_settings dict!
        custom_settings = getattr(spider, "custom_settings", {})

        if custom_settings is None:
            custom_settings = {}

        return custom_settings.get("USER_AGENT")

    def process_request(self, request, spider):
        specific_spider_user_agent = self.get_specific_spider_user_agent(spider)
        if specific_spider_user_agent is not None:
            # The spider has specificed a specific user agent!
            # Given that it has specified a specific one, then we probably shouldn't mess around
            # with randomising.
            return

        is_fixed = getattr(spider, "fixed_user_agent_onstart", self.fixed_user_agent_onstart)

        if is_fixed:
            spider_user_agent = getattr(spider, "fixed_user_agent", None)
            if spider_user_agent is None:
                spider_user_agent = self.user_agent_rotator.get_random_user_agent()
                setattr(spider, "fixed_user_agent", spider_user_agent)
            request.headers["User-Agent"] = spider_user_agent

        else:
            request.headers["User-Agent"] = self.user_agent_rotator.get_random_user_agent()
