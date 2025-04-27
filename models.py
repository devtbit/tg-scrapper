import os

from peewee import (
    CharField,
    DateField,
    ForeignKeyField,
    Model,
    SqliteDatabase,
)

database_name = os.environ.get("TG_DB_NAME", "telegram.db")

db = SqliteDatabase(database_name)


class Message(Model):
    group = CharField(null=True)
    message_id = CharField(null=True)
    grouped_id = CharField(null=True)
    reply_to_message_id = CharField(null=True)
    sender_id = CharField(null=True)
    sender_name = CharField(null=True)
    message = CharField(null=True)
    message_date = DateField(null=True)
    message_media = CharField(null=True)
    fwd_source_id = CharField(null=True)
    fwd_source_name = CharField(null=True)

    class Meta:
        database = db


class Media(Model):
    message = ForeignKeyField(Message, backref='media')
    name = CharField()
    file_location = CharField()

    class Meta:
        database = db
