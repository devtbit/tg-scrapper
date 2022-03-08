#!/usr/bin/env python

import datetime, os
import shutil

from telegram import Telegram
from s3 import S3
from utils import load_range_params, clean_prefix, create_dirs, is_in_range, update_csv

api_phone_number = os.environ['API_PHONE_NUMBER']
api_id = os.environ['API_ID']
api_hash = os.environ['API_HASH']
groups = [g for g in os.environ['TG_GROUPS'].split(',')]
cloud_backup = 'S3_UPLOAD' in os.environ and os.environ['S3_UPLOAD'] == "true"
cleanup = 'CLEAN_DATA' in os.environ and os.environ['CLEAN_DATA'] == "true"
date_range = load_range_params(os.environ)

timestamp = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M")
timestamp_prefix = str(timestamp)

print("connecting to telegram...")
tg = Telegram(api_phone_number, api_id, api_hash)

bucket = None
if cloud_backup:
    bucket = S3(os.environ['S3_BUCKET'])

async def main():
    for group in groups:
        print(f"processing {group}")
        group_prefix = clean_prefix(group)
        group_dir = f"./data/{group_prefix}"
        file_prefix = f"{group_prefix}_{timestamp_prefix}"
        media_dir = f"{group_dir}/{file_prefix}_media"
        csv_archive = f"{group_dir}/{file_prefix}_archive.csv"
        create_dirs([group_dir, media_dir])
        rows = []
        try:
            async for message in tg.iter_chat(group):
                if message is not None:
                    data, message_timestamp = tg.process_message(message)
                    if is_in_range(date_range, message_timestamp):
                        if message.media:
                            media, filename = await tg.download_message_media(message, media_dir)
                            object_name = f"{group}/{file_prefix}_media/{filename}"
                            if cloud_backup:
                                print("uploading media to s3...")
                                bucket.upload(object_name, media)
                        else:
                            filename = None
                        
                        data[-1] = filename
                        print(data)
                        rows.append(data)
                        update_csv(rows, csv_archive)
        except Exception as e:
            print(e)

        if cloud_backup:
            print("uploading csv archive to s3...")
            bucket.upload(f"{group}/{file_prefix}_archive.csv", csv_archive)

        if cleanup:
            shutil.rmtree(group_dir)

        print(f"completed {group}")

with tg.client:
    tg.client.loop.run_until_complete(main())
