#!/usr/bin/env python

import os

from scrapper import Scrapper

groups = [g for g in os.environ['TG_GROUPS'].split(',')]
upload = 'S3_UPLOAD' in os.environ and os.environ['S3_UPLOAD'] == "true"
cleanup = 'CLEAN_DATA' in os.environ and os.environ['CLEAN_DATA'] == "true"

tg_creds = {
    'api_phone_number': os.environ['API_PHONE_NUMBER'],
    'api_id': os.environ['API_ID'],
    'api_hash': os.environ['API_HASH'],
}

scrapper = Scrapper(
    tg_creds,
    groups,
    s3_upload=upload,
    bucket_name=os.environ['S3_BUCKET'],
    post_cleanup=cleanup,
)
scrapper.set_date_range(os.environ)

with scrapper.tg.client:
    scrapper.tg.client.loop.run_until_complete(scrapper.scrape_groups(verbose=True))
