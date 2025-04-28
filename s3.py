#!/usr/bin/env python
import boto3


class S3:
    def __init__(self, bucket):
        self.client = boto3.client('s3')
        self.bucket = bucket

    def upload(self, object_name, file):
        return self.client.upload_file(
            file,
            self.bucket,
            object_name,
        )

    def upload_bytes(self, object_name, bytes):
        return self.client.put_object(
            Bucket=self.bucket,
            Key=object_name,
            Body=bytes,
        )
