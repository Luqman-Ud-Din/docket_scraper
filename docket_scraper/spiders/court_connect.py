import re
from datetime import datetime
from string import ascii_lowercase

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
from w3lib.url import url_query_cleaner

from docket_scraper.helpers import strip_text, reset_cookies
from docket_scraper.spiders.base_spider import BaseParseSpider, BaseCrawlSpider


class CourtConnectParseParseSpider(BaseParseSpider):
    name = 'court-connect-parse'

    def parse(self, response, **kwargs):
        docket = {
            'url': response.url,
            'id': self.parse_id(response),
            'start_date': self.parse_start_date(response),
            'end_date': self.parse_end_date(response),
            'title': self.parse_title(response),
            'filing_date': self.parse_filing_date(response),
            'type': self.parse_type(response),
            'status': self.parse_status(response),
            'parties': self.parse_parties(response),
            'entries': self.parse_entries(response),
        }

        for entry in docket['entries']:
            if not entry['party']:
                continue

            party = next(
                filter(lambda party: entry['party'] == party['name'], docket['parties']),
                None
            )

            if not party:
                raise Exception('Unable to find entry party in corresponding parties')

            entry['party'] = party['id']

        return docket

    def parse_id(self, response):
        item_id_css = '[NAME="selection"] + table td:contains("Case ID") + td::text'
        return strip_text(response.css(item_id_css).extract())[0]

    def parse_start_date(self, response):
        date_css = '[NAME="selection"] + table td:contains("Docket Start Date") + td::text'
        return next(iter(strip_text(response.css(date_css).extract())), None)

    def parse_end_date(self, response):
        date_css = '[NAME="selection"] + table td:contains("Docket Ending Date") + td::text'
        return next(iter(strip_text(response.css(date_css).extract())), None)

    def parse_title(self, response):
        title_css = '[NAME="description"] + table td:contains("Case ID") + td::text'
        raw_title = strip_text(response.css(title_css).extract())[0]
        item_id = self.parse_id(response)
        return strip_text(re.sub(rf'^({item_id}|\s|-)*', '', raw_title, flags=re.S))

    def parse_filing_date(self, response):
        date_css = '[NAME="description"] + table td:contains("Filing Date") + td::text'
        filing_date = strip_text(response.css(date_css).extract())[0]
        filing_date = re.sub(r'\s*,\s*|(st|nd|rd|th),', ',', filing_date)
        return datetime.strptime(filing_date, '%A,%B %d, %Y').isoformat()

    def parse_type(self, response):
        type_css = '[NAME="description"] + table td:contains("Type") + td::text'
        return strip_text(response.css(type_css).extract())[0]

    def parse_status(self, response):
        status_css = '[NAME="description"] + table td:contains("Status") + td::text'
        raw_status = strip_text(response.css(status_css).extract())[0]
        return strip_text(raw_status.split('-'))[0]

    def parse_parties(self, response):
        css_1 = '[NAME="parties"] + table tr[valign]:not([align])'
        css_2 = '[NAME="parties"] + table tr[valign][align]'

        parties = []
        for party_selector_1, party_selector_2 in zip(response.css(css_1), response.css(css_2)):
            party_associates = strip_text(party_selector_1.css('td:nth-child(2) ::text').extract())
            party_end_date = strip_text(party_selector_1.css('td:nth-child(3) ::text').extract())
            party_type = strip_text(party_selector_1.css('td:nth-child(4) ::text').extract())
            party_id = strip_text(party_selector_1.css('td:nth-child(5) ::text').extract())
            party_name = strip_text(party_selector_1.css('td:nth-child(6) ::text').extract())
            party_address = '\n'.join(strip_text(party_selector_2.css('td:nth-child(2) ::text').extract()))
            party_aliases = filter(
                lambda t: t.lower() != 'none',
                strip_text(party_selector_2.css('td:nth-child(4) ::text').extract())
            )

            party = {
                'associates': next(iter(party_associates), None),
                'end_date': next(iter(party_end_date), None),
                'type': next(iter(party_type), None),
                'id': next(iter(party_id), None),
                'name': next(iter(party_name), None),
                'address': party_address or None,
                'aliases': next(party_aliases, None)
            }

            parties.append(party)

        for party in parties:
            associates = strip_text((party['associates'] or '').split(','))
            party['associates'] = [parties[int(associate) - 1]['id'] for associate in associates]

        return parties

    def parse_entries(self, response):
        css_1 = '[NAME="dockets"] + table tr[valign]'
        css_2 = '[NAME="dockets"] + table tr[valign] + tr'

        entries = []
        for entry_selector_1, entry_selector_2 in zip(response.css(css_1), response.css(css_2)):
            entry_filing_date = ' '.join(strip_text(entry_selector_1.css('td:nth-child(1) ::text').extract()))
            entry_description = '\n'.join(strip_text(entry_selector_1.css('td:nth-child(2) ::text').extract()))
            entry_party = strip_text(entry_selector_1.css('td:nth-child(3) ::text').extract())
            entry_monetary = '\n'.join(strip_text(entry_selector_1.css('td:nth-child(4) ::text').extract()))
            entry_content = '\n'.join(strip_text(entry_selector_2.css('td:nth-child(2) ::text').extract()))

            if entry_filing_date:
                entry_filing_date = datetime.strptime(entry_filing_date, '%d-%b-%Y %I:%M %p').isoformat()

            entry = {
                'filing_date': entry_filing_date or None,
                'description': entry_description or None,
                'party': next(iter(entry_party), '').strip(',') or None,
                'monetary': entry_monetary or None,
                'content': entry_content if entry_content.lower() != 'none.' else None
            }
            entries.append(entry)

        return entries


def process_item_url(url):
    url = url_query_cleaner(url, ['case_id'])
    return url.replace('/ck_public_qry_doct.cp_dktrpt_frames', '/ck_public_qry_doct.cp_dktrpt_docket_report')


def process_pagination_url(url):
    url = url_query_cleaner(url, ['backto', 'partial_ind', 'last_name', 'case_type', 'PageNo'])

    if '/cc/cconnect/' not in url:
        url = url.replace('courtconnect.courts.delaware.gov/', 'courtconnect.courts.delaware.gov/cc/cconnect/')

    return url.replace('/ck_public_qry_doct.cp_dktrpt_frames', '/ck_public_qry_doct.cp_dktrpt_docket_report')


start_url_t = 'https://courtconnect.courts.delaware.gov/cc/cconnect/ck_public_qry_cpty.cp_personcase_srch_details?' \
              'backto=P&partial_ind=checked&last_name={}&case_type=ALL&PageNo=1'


class CourtConnectCrawlSpider(BaseCrawlSpider):
    name = 'court-connect-crawl'
    parse_spider = CourtConnectParseParseSpider()

    start_urls = [start_url_t.format(character) for character in ascii_lowercase]
    allowed_domains = ['courtconnect.courts.delaware.gov']

    item_css = '[href*="case_id="]'
    listings_css = ['[href*=cp_personcase_srch_details]']

    rules = [
        Rule(
            LinkExtractor(
                restrict_css=item_css,
                process_value=process_item_url
            ),
            process_request=reset_cookies,
            callback='parse_item'
        ),
        Rule(
            LinkExtractor(
                restrict_css=listings_css,
                process_value=process_pagination_url
            ),
            process_request=reset_cookies,
            callback='parse'),
    ]
