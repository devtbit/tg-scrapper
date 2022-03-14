#!/usr/bin/env python

import datetime
import os
import shutil

from telegram import Telegram
from s3 import S3
from utils import create_dirs, is_in_range, load_range_params, update_csv

class Scrapper:

    def __init__(self,
        target_groups=[],
        s3_upload=False,
        bucket_name=None,
        post_cleanup=False,
        date_range=None,
    ):
        self.telegram = Telegram()
        self.target_groups = target_groups
        self.bucket = None
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
        group_entity = self.telegram.get_group_entity(group)
        if group_entity is None:
            raise Exception('group not found in the groups you are part of')
        self.group = group
        self.group_entity = group_entity

    def get_groups(self, megagroup=False):
        return self.telegram.get_groups(megagroup=megagroup)
    
    def list_groups(self, megagroup):
        groups = self.get_groups(megagroup=megagroup)
        for group in groups:
            if type(group).__name__ == "ChatForbidden" or group.username is None:
                print(f"({group.id}) {group.title}")
            else:
                print(group.username)

    async def get_group_members(self, limit=None):
        if not self.group_entity: raise Exception('set target first')
        members = await self.telegram.get_members(self.group_entity, limit=limit)
        if members is not None and len(members) > 0:
            return [[
                u.username,
                u.id,
                f"{u.first_name} {u.last_name}".strip(),
                self.group,
            ] for u in members]
        return []

    async def dump_members(self, limit=None):
        if not self.group: raise Exception('set target first')
        directory, fileprefix, prefix = self.create_group_workspace(self.group)
        csv_archive = f"{fileprefix}_members_archive.csv"
        members = await self.get_group_members(limit=limit)
        if len(members) > 0:
            update_csv(members, csv_archive, columns=['username','id','name','group'])
            if self.bucket:
                self.bucket.upload(f"{self.group}/{prefix}_members_archive.csv", csv_archive)
        else:
            print("memberlist not available")

    def get_workspace(self, data_dir="./data"):
        if not self.group: raise Exception('set target first')
        directory = f"{data_dir}/{self.group}"
        prefix = f"{self.group}_{str(self.timestamp)}"
        return directory, f"{directory}/{prefix}", prefix

    def create_group_workspace(self,
        group,
    ):
        self.set_target(group)
        directory, fileprefix, prefix = self.get_workspace()
        media = f"{fileprefix}_media"
        create_dirs([media])
        return directory, fileprefix, prefix

    def iter_group(self):
        if not self.group_entity: raise Exception('set target first')
        return self.telegram.iter_chat(self.group_entity, offset_date=self.date_range["to"]["timestamp"])

    def is_in_scope(self, timestamp):
        in_range = is_in_range(self.date_range, timestamp)
        return in_range

    def teardown_workspace(self):
        if self.post_cleanup:
            directory, _, _ = self.get_workspace()
            shutil.rmtree(directory)

    async def handle_media(self, message):
        filename = None
        if message.media:
            _, fileprefix, prefix = self.get_workspace()
            media, filename = await self.telegram.download_message_media(message, f"{fileprefix}_media")
            if media is None:
                return None
            object_name = f"{self.group}/{prefix}_media/{filename}"
            if self.bucket:
                self.bucket.upload(object_name, media)
                if self.post_cleanup:
                    os.remove(media)
        return filename

    async def process_message(self, message, verbose=False):
        data, timestamp = self.telegram.process_message(message)
        
        if not self.is_in_scope(timestamp): return False, None
        
        media = await self.handle_media(message)
        data[-1] = media

        if message.forward is not None and \
            message.forward.original_fwd.from_id is not None:
            try:
                source = await self.telegram.client.get_entity(
                    message.forward.original_fwd.from_id,
                )
                data.append(source.id)
                data.append(source.title)
            except Exception as e:
                fwd_id = message.forward.original_fwd.from_id
                if verbose: print(f"WARN: forward is private or cannot be accessed ({fwd_id})")
                data.append(fwd_id)
                data.append(None)
        else:
            data.append(None)
            data.append(None)

        if verbose: print(data)
        return True, data

    async def scrape_group(self, group, verbose=False):
        if group not in self.target_groups: raise Exception('group not in targets')
        if verbose: print(f"processing {group}")
        directory, fileprefix, prefix = self.create_group_workspace(group)
        csv_archive = f"{fileprefix}_archive.csv"
        await self.dump_members()
        rows = []
        try:
            async for message in self.iter_group():
                if message is None: continue
                in_scope, data = await self.process_message(message, verbose=verbose)
                if in_scope:
                    rows.append(data)
                    update_csv(rows, csv_archive)
        except Exception as e:
            print(e)
            raise Exception('failed to scrape groups')
            
        if self.bucket:
            self.bucket.upload(f"{group}/{prefix}_archive.csv", csv_archive)
 
        if verbose: print(f"completed {group}")

    async def scrape_groups(self, verbose=False):
        for group in self.target_groups:
            await self.scrape_group(group, verbose=verbose)

    async def identify(self, phone_number, verbose=False):
        try:
            entity = await self.telegram.client.get_entity(phone_number)
        except Exception as e:
            if "Cannot find" in str(e):
                print("User not found")
                return None
            else:
                raise e

        if verbose: print(entity.username)
        return entity.username
