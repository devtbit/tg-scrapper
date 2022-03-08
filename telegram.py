#!/usr/bin/env python

import os

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.utils import get_display_name

from utils import process_date

class Telegram:
    def __init__(self,
            phone_number,
            api_id,
            api_hash,
            verify=False
        ):
        client = TelegramClient(phone_number, api_id, api_hash)
        client.connect()

        if not client.is_user_authorized():
            if verify:
                client.send_code_request(phone_number)
                client.sign_in(phone_number, input('code: '))
            else:
                raise Exception('session is not authorized')
        self.client = client

    def get_chat_groups(self, offset_date=None, offset_id=0, limit=200):
        result = self.client(GetDialogsRequest(
            offset_date=offset_date,
            offset_id=offset_id,
            offset_peer=InputPeerEmpty(),
            limit=limit,
            hash=0,
        ))
        return result.chats

    def process_message(self, message, as_dict=False):
        timestamp, date = process_date(
            message.date.year,
            message.date.month,
            message.date.day,
            message.date.hour,
            message.date.minute,
        )
        sender_name = get_display_name(message.sender)
        if as_dict:
            return {
                'sender_name': sender_name,
                'sender_id': message.from_id,
                'message_id': message.id,
                'message_timestamp': timestamp,
                'message_date': date,
                'message': message.text,
            }

        return [self.current_group,
                message.id,
                message.from_id,
                sender_name,
                f"\"{message.text}\"",
                date,
                None], timestamp

    def iter_chat(self, group):
        self.current_group = group
        return self.client.iter_messages(group)

    async def download_message_media(self, message, location):
        media_path = await message.download_media(file=location)
        base_name = os.path.basename(media_path)
        return media_path, base_name

    def get_credentials():
        return {
            'api_phone_number': os.environ['API_PHONE_NUMBER'],
            'api_id': os.environ['API_ID'],
            'api_hash': os.environ['API_HASH'],
        }
