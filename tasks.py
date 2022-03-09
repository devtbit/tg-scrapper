#!/usr/bin/env python

import os
from invoke import task

from scrapper import Scrapper
from telegram import Telegram

@task(help={
    'phone_number': "The phone number to identify",
})
def identify(c,
    phone_number,
):
    """
    Identifies a phone number against a Telegram user.
    """
    scrapper = Scrapper()
    with scrapper.telegram.client:
        scrapper.telegram.client.loop.run_until_complete(
            scrapper.identify(phone_number, verbose=True)
        )

@task(help={
    'megagroup': "Only display mega-groups",
})
def list_groups(c, megagroup=False):
    """
    Lists the groups the current user is a member of.
    """
    scrapper = Scrapper()
    scrapper.list_groups(megagroup=megagroup)

@task(help={
    'group': "Group to dump the member list from",
    'limit': "Limit the number of members to be dumped (default all)",
})
def dump_member_list(c, group, limit=0):
    """
    Dumps the list of members of a group.
    """
    scrapper = Scrapper()
    scrapper.create_group_workspace(group)
    with scrapper.telegram.client:
        scrapper.telegram.client.loop.run_until_complete(
            scrapper.dump_members(limit=limit if limit > 0 else None)
        )

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
    Scrapes all the messages of a list of Telegram groups between the
    given date range. Groups must be either public or with access given to the
    current user. If member list is available it will also be dumped.
    """
    groups = [g for g in targets.split(',')]
    scrapper = Scrapper(
        groups,
        s3_upload=upload,
        bucket_name=bucket,
        post_cleanup=cleanup,
    )
    scrapper.set_date_range(from_date, to_date)

    with scrapper.telegram.client:
        scrapper.telegram.client.loop.run_until_complete(
            scrapper.scrape_groups(verbose=verbose)
        )

@task
def verify_session(c):
    """
    Verifies the session with a code sent through Telegram.
    Requires manual user input.
    """
    return Telegram(verify=True)
