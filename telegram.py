#!/usr/bin/env python

import os

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.channels import GetParticipantsRequest, GetChannelsRequest
from telethon.tl.types import InputPeerEmpty, ChannelParticipantsRecent
from telethon.utils import get_display_name

from utils import process_date

class Telegram:
    def __init__(self,
            credentials=None,
            verify=False
        ):
        if credentials is None:
            credentials = Telegram.get_credentials()

        client = TelegramClient(
            credentials['api_phone_number'],
            credentials['api_id'],
            credentials['api_hash'],
        )
        client.connect()

        if not client.is_user_authorized():
            if verify:
                client.send_code_request(credentials['api_phone_number'])
                client.sign_in(credentials['api_phone_number'], input('code: '))
            else:
                raise Exception('session is not authorized')
        self.client = client
        self.groups = self.fetch_chat_groups()

    def fetch_chat_groups(self, offset_date=None, offset_id=0, limit=200):
        result = self.client(GetDialogsRequest(
            offset_date=offset_date,
            offset_id=offset_id,
            offset_peer=InputPeerEmpty(),
            limit=limit,
            hash=0,
        ))
        return result.chats

    async def fetch_group(self, group):
        result = await self.client(GetChannelsRequest(
            id=[group]
        ))
        if len(result.chats) > 0:
            return result.chats[0]
        return None

    def get_groups(self, megagroup=False):
        if megagroup:
            return [g for g in self.groups if (
                type(g).__name__ != "ChatForbidden" and
                g.megagroup == True
            )]
        return self.groups

    async def get_group_entity(self, group):
        for g in self.groups:
            if group == str(g.id) or group == g.title or (
                type(g).__name__ != "ChatForbidden" and
                (
                    group == g.username # or
                )
            ):
                if type(g).__name__ == "ChatForbidden":
                    raise Exception('ChatForbidden is not supported for scrapping')
                return g
        return await self.fetch_group(group)

    async def get_members(self, group, default_size=200):
        if group.megagroup:
            if group.participants_count is None or group.participants_count < default_size:
                result = await self.client.get_participants(group)
                return result
            else:
                participants = []
                fetched = 0
                while fetched < group.participants_count:
                    result = await self.client(GetParticipantsRequest(
                        channel=group,
                        filter=ChannelParticipantsRecent(),
                        offset=fetched,
                        limit=default_size,
                        hash=0
                    ))
                    if len(result.users) == 0:
                        break
                    fetched += len(result.users)
                    participants.extend(result.users)
                return participants
        return []

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

        return [self.current_group.id,
                message.id,
                message.from_id.user_id 
                    if type(message.from_id).__name__ == "PeerUser" 
                    else message.from_id,
                sender_name,
                f"\"{message.text}\"",
                date,
                None], timestamp

    def iter_chat(self, group, offset_date=None):
        self.current_group = group
        return self.client.iter_messages(group, offset_date=offset_date)

    async def download_message_media(self, message, location):
        media_path = await message.download_media(file=location)
        if media_path is None:
            return None, None
        base_name = os.path.basename(media_path)
        return media_path, base_name

    def get_credentials():
        return {
            'api_phone_number': os.environ['API_PHONE_NUMBER'],
            'api_id': os.environ['API_ID'],
            'api_hash': os.environ['API_HASH'],
        }
