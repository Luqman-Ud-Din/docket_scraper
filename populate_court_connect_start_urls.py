import time
from string import ascii_lowercase

import redis

r = redis.Redis(host='docket-redis', port=6379, db=0)
r.flushdb()

start_url_t = 'https://courtconnect.courts.delaware.gov/cc/cconnect/ck_public_qry_cpty.cp_personcase_srch_details?' \
              'partial_ind=checked&last_name={}&case_type=ALL&PageNo=1'

for character in ascii_lowercase:
    start_url = start_url_t.format(character)
    r.lpush('court-connect-crawl:start_urls', start_url)
    time.sleep(1)
