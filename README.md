# Telegram Scrapper

Utility tool to scrape Telegram groups/channels. It downloads the messages of a group within a date range, it will also download all the media/files of the messages. Everything can be optionally uploaded to a S3 bucket.

This tool was created with a focus on automation and containerization. The idea behind this tool was inspired by https://github.com/jordanwildon/Telepathy

### Requirements

This tool requires to be registered in Telegram API. API ID and API Hash are required for this to work. These values are provided through environment variables:

* API_PHONE_NUMBER
* API_ID
* API_HASH

### Install

```
pip install -r requirements.txt
```

### Examples

Display the list of groups current user is member of:
```
inv list-groups
```

Scrape two groups from 2022-01-01 to 2022-03-01 and print every message:
```
inv scrape-groups --targets=MySecretGroup,MyOtherSecretGroup -f 2022-01-01 -t 2022-03-01 -v
```

The next command requires AWS CLI with credentials configured (note that account only requires PutObject permissions to the bucket).
Scrape one group from 2022-02-28 to 2022-03-01 and upload everything to a S3 Bucket named MY_BUCKET (NOTE: -c will delete every file downloaded locally):
```
inv scrape-groups --targets=MySecretGroup -f 2022-02-28 -t 2022-03-01 -v -u -b MY_BUCKET -c
```

## Docker

The tool can also be dockerized:

Build the image:
```
docker build -f Dockerfile -t tg-scrapper:latest .
```

Create a shortcut/alias (AWS variables only needed to upload to S3):
```
alias tg="docker run -e "AWS_REGION=us-east-1" -e "AWS_ACCESS_KEY_ID=XXXXXXXXX" -e "AWS_SECRET_ACCESS_KEY=XXXXXXXXX" -e "API_PHONE_NUMBER=+1XXXXXXXX" -e "API_ID=XXXXXXXXXX" -e "API_HASH=XXXXXXXXXXXXX" -v $PWD/data:/tg/data --rm -it --name tg-scrapper tg-scrapper:latest"
```

Run it:
```
tg scrape-groups --targets=MySecretGroup -f 2022-02-28 -t 2022-03-01 -v
```

## AWS ECS (Docker compose)

The tool can also be run on a ECS Container Task with docker compose. Follow the instructions at https://docs.docker.com/cloud/ecs-integration/ to set up your docker instance (specifically setup your AWS credentials, create your ECS context and set up your Image Repository credentials on AWS Secret Manager).

Then create an .env file for Docker compose with the following variables (fill with your own values):
```
AWS_REGION=XXXXXXX
AWS_ACCESS_KEY_ID=XXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXXX
API_PHONE_NUMBER=XXXXXXXXXX
API_ID=XXXXXXXX
API_HASH=XXXXXXXX
TG_GROUPS=MySecretGroup,MyOtherSecretGroup
FROM_DATE=XXXXXXX
TO_DATE=XXXXXXXXXX
S3_BUCKET=XXXXXXXXX
IMAGE=myuser/tg-scrapper:latest
IMAGE_REPO_SM=arn:aws:secretsmanager:XXXXXXXXXXXXX
```

Build your image:
```
docker build -f Dockerfile -t myuser/tg-scrapper:latest .
```
NOTE: if you are building from an ARM device pass ```--platform linux/amd64``` to avoid issues.

Push your image to your repository:
```
docker image push myuser/tg-scrapper:latest
```

Then create your ECS cluster with the following command:
```
docker compose --env-file .env --file docker-compose.yml up
```

Please note that this might not be an efficient approach of running long tasks/jobs and is prone to failures. Use at your own risk.
