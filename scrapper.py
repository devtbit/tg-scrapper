#!/usr/bin/env python

import datetime
import os
import shutil

from telegram import Telegram
from s3 import S3
from utils import clean_prefix, create_dirs, is_in_range, load_range_params, update_csv

class Scrapper:

    def __init__(self,
        credentials,
        target_groups,
        s3_upload=False,
        bucket_name=None,
        post_cleanup=False,
        date_range=None,
    ):
        self.tg = Telegram(
            credentials['api_phone_number'],
            credentials['api_id'],
            credentials['api_hash'],
        )
        self.target_groups = target_groups

        if s3_upload:
            self.bucket = S3(bucket_name)
        self.post_cleanup = post_cleanup
        self.date_range = date_range
        self.timestamp = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M")
        self.group = None

    def set_date_range(self, from_date, to_date):
        fd = from_date.split('-')
        td = to_date.split('-')
        params = {
            'FROM_YEAR': fd[0],
            'FROM_MONTH': fd[1],
            'FROM_DAY': fd[2],
            'TO_YEAR': td[0],
            'TO_MONTH': td[1],
            'TO_DAY': td[2],
        }
        self.date_range = load_range_params(params)

    def set_target(self, group):
        self.group = group

    def get_fileprefix(self, data_dir="./data"):
        if not self.group: raise Exception('set target first')
        directory = f"{data_dir}/{self.group}"
        prefix = f"{self.group}_{str(self.timestamp)}"
        return directory, f"{directory}/{prefix}", prefix

    def create_group_workspace(self,
        group,
    ):
        group = clean_prefix(group)
        self.set_target(group)
        directory, fileprefix, prefix = self.get_fileprefix()
        media = f"{fileprefix}_media"
        create_dirs([media])
        return directory, fileprefix, prefix

    def iter_group(self):
        return self.tg.iter_chat(self.group)

    async def handle_media(self, message):
        filename = None
        if message.media:
            _, fileprefix, prefix = self.get_fileprefix()
            media, filename = await self.tg.download_message_media(message, f"{fileprefix}_media")
            object_name = f"{self.group}/{prefix}_media/{filename}"
            if self.bucket:
                self.bucket.upload(object_name, media)
        return filename

    def is_in_scope(self, timestamp):
        return is_in_range(self.date_range, timestamp)

    async def scrape_groups(self, verbose=False):
        for group in self.target_groups:
            if verbose: print(f"processing {group}")
            directory, fileprefix, prefix = self.create_group_workspace(group)
            csv_archive = f"{fileprefix}_archive.csv"
            rows = []
            try:
                async for message in self.iter_group():
                    if message is not None:
                        data, timestamp = self.tg.process_message(message)
                        if self.is_in_scope(timestamp):
                            media = await self.handle_media(message)
                            data[-1] = media
                            if verbose: print(data)
                            rows.append(data)
                            update_csv(rows, csv_archive)
            except Exception as e:
                print(e)
                raise Exception('failed to scrape groups')
            
            if self.bucket:
                self.bucket.upload(f"{group}/{prefix}_archive.csv", csv_archive)

            if self.post_cleanup:
                shutil.rmtree(directory)
            
            if verbose: print(f"completed {group}")
