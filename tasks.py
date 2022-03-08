#!/usr/bin/env python

import os
from invoke import task

from scrapper import Scrapper
from telegram import Telegram

@task(help={
    'from_date': "Date to start scraping from (YYYY-MM-DD)",
    'to_date': "Date to end the scraping (YYYY-MM-DD)",
    'targets': "List of groups to scrape from (comma separated, no whitespaces)",
    'bucket': "S3 Bucket to upload messages & media (requires upload flag)",
    'upload': "Flag to indicate that outputs need to be uploaded (requires bucket)",
    'cleanup': "Delete all files when done",
    'verbose': "Output additional info",
})
def scrape_groups(c,
        from_date,
        to_date,
        targets="",
        bucket=None,
        upload=False,
        cleanup=False,
        verbose=False,
):
    """
    Scrapes all the messages of a list of groups between the
    given date range.
    """
    groups = [g for g in targets.split(',')]
    credentials = Telegram.get_credentials()
    scrapper = Scrapper(
        credentials,
        groups,
        s3_upload=upload,
        bucket_name=bucket,
        post_cleanup=cleanup,
    )
    scrapper.set_date_range(from_date, to_date)

    with scrapper.tg.client:
        scrapper.tg.client.loop.run_until_complete(
            scrapper.scrape_groups(verbose=verbose)
        )

@task
def verify_session(c):
    """
    Verifies the session with a code sent through Telegram.
    Requires manual user input.
    """
    credentials = Telegram.get_credentials()
    return Telegram(
        credentials['api_phone_number'],
        credentials['api_id'],
        credentials['api_hash'],
        verify=True
    )