import re

from scrapy import Request
from scrapy.link import Link
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule, Spider
from w3lib.url import add_or_replace_parameter, url_query_cleaner


def strip_text(text_or_list):
    text_or_list = text_or_list or ''

    if isinstance(text_or_list, str):
        return text_or_list.strip()

    stripped_texts = []
    for raw_text in text_or_list:
        stripped_text = (raw_text or '').strip()
        if stripped_text:
            stripped_texts.append(stripped_text)

    return stripped_texts


class TrialParseSpider(Spider):
    name = 'trial-parse'

    def parse(self, response, *kwargs):
        return {
            'item_id': self.parse_item_id(response),
            'url': response.url,
            'artist': self.parse_artists(response),
            'title': self.parse_title(response),
            'image': self.parse_image(response),
            'height': self.parse_height(response),
            'width': self.parse_width(response),
            'description': self.parse_description(response),
            'categories': self.parse_categories(response),
        }

    def parse_item_id(self, response):
        return re.findall(r'/item/(\d+)/', response.url)[0]

    def parse_categories(self, response):
        return [link_text for link_text, _ in response.meta.get('browse_tree') or [] if link_text]

    def parse_title(self, response):
        title_css = '#content h1::text'
        return response.css(title_css).get()

    def parse_image(self, response):
        image_css = '#body img::attr(src)'
        return response.urljoin(response.css(image_css).get())

    def parse_description(self, response):
        description_css = '.description ::text'
        return '\n'.join(strip_text(response.css(description_css).getall()))

    def parse_artists(self, response):
        artists_css = '.artist::text'
        artists_re = r':([^;$]+)'
        return strip_text(response.css(artists_css).re(artists_re)) or []

    def parse_dimensions(self, response):
        dimensions_css = '.properties td:contains(Dimensions)+td::text'
        dimensions_re = r'([\.\s\dx×]+)cm'
        raw_dimensions = response.css(dimensions_css).re_first(dimensions_re) or ''
        return strip_text(re.split(r'x|×', raw_dimensions.lower(), flags=re.I))

    def parse_width(self, response):
        dimensions = self.parse_dimensions(response)
        if len(dimensions) == 2:
            return float(dimensions[0])
        elif len(dimensions) == 3:
            return float(dimensions[1])

    def parse_height(self, response):
        dimensions = self.parse_dimensions(response)
        if len(dimensions) == 2:
            return float(dimensions[1])
        elif len(dimensions) == 3:
            return float(dimensions[2])


class PaginationLinkExtractor:
    def extract_links(self, response):
        page_selector = response.css('form.nav.next')
        if not page_selector:
            return []

        if not response.css('[href*="item/"]'):
            return []

        page_selector = page_selector[0]
        next_page_number = page_selector.css('[name=page]::attr(value)').get()
        next_page_url = response.urljoin(page_selector.css('::attr(action)').get())
        next_page_url = add_or_replace_parameter(next_page_url, 'page', next_page_number)

        return [Link(next_page_url)]


class TrialCrawlSpider(CrawlSpider):
    name = 'trial-crawl'
    parse_spider = TrialParseSpider()
    seen_item_ids = set()

    allowed_domains = ['pstrial-2019-12-16.toscrape.com']
    start_urls = [
        'http://pstrial-2019-12-16.toscrape.com/browse/'
    ]

    item_css = 'div>[href*=item]'
    # forcing to child categories link to be extracted from parent categories page
    # for better browse tree
    listings_xpath = ['//div[@id="subcats"]//a[descendant-or-self::h3]']
    allowed_listings = ['/insunsh', '/summertime']

    rules = [
        Rule(LinkExtractor(restrict_css=item_css, process_value=url_query_cleaner), callback='parse_item'),
        Rule(LinkExtractor(restrict_xpaths=listings_xpath, allow=allowed_listings), callback='parse'),
        Rule(PaginationLinkExtractor(), callback='parse'),
    ]

    def parse(self, response, **kwargs):
        for request_or_item in self._parse_response(response, None, {}):
            if isinstance(request_or_item, Request):
                request_or_item.meta['browse_tree'] = self.generate_browse_tree(response)
            yield request_or_item

    def parse_item(self, response):
        item_id = self.parse_spider.parse_item_id(response)
        if self.is_seen_item(item_id):
            return

        return self.parse_spider.parse(response)

    def generate_browse_tree(self, response):
        browse_tree = [(response.meta.get('link_text', ''), response.url)]
        return response.meta.get('browse_tree', []) + browse_tree

    def is_seen_item(self, item_id):
        if item_id in self.seen_item_ids:
            return True

        self.seen_item_ids.add(item_id)
