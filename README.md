# Telegram Scrapper

Utility tool to scrape Telegram groups/channels. It downloads the messages of a group within a date range, it will also download all the media/files of the messages. Everything can be optionally uploaded to a S3 bucket.

This tool was created with a focus on automation and containerization. The idea behind this tool was inspired by https://github.com/jordanwildon/Telepathy

### Requirements

This tool depends on Telethon and is required to be registered in Telegram API. Credentials are provided through environment variables. To set the variables:

```
export API_PHONE_NUMBER=XXXXXXXXXX
export API_ID=XXXXXXXXXX
export API_HASH=XXXXXXXXXX
```

To obtain API credentials go to: my.telegram.org

AWS CLI can optionally be installed in order to upload data to a S3 Bucket.

#### Install dependencies 

```
pip install -r requirements.txt
```

### Usage

Tool uses invoke to run tasks:
```
$> inv --list

Available tasks:

  dump-member-list   Dumps the list of members of a group.
  identify           Identifies a phone number against a Telegram user.
  list-groups        Lists the groups the current user is a member of.
  scrape-groups      Scrapes all the messages of a list of Telegram groups between the given date range.
  verify-session     Verifies the session with a code sent through Telegram.
```

#### Examples

Validate your session before running any other command (if you haven't):
```
inv verify-session
```
Telethon will generate session files that can be reused.

Scrape two groups from 2022-01-01 to 2022-03-01 and display every message:
```
inv scrape-groups --targets=MySecretGroup,MyOtherSecretGroup -f 2022-01-01 -t 2022-03-01 -v
```
This command will fetch all memebers of the groups (if possible) and all messages and store them in 2 CSV files. It will also downlad all media files from messages. CSV files and media folders will be prefixed by a timestamp for unique identification across runs.

The next command requires AWS CLI with credentials configured (note that account only requires PutObject permissions to the bucket).
Scrape one group from 2022-02-28 to 2022-03-01 and upload everything to a S3 Bucket named MY_BUCKET (NOTE: -c will delete every file downloaded/generated locally):
```
inv scrape-groups --targets=MySecretGroup -f 2022-02-28 -t 2022-03-01 -v -u -b MY_BUCKET -c
```

## Docker

The tool can also be dockerized. It is recommended to generate the Telethon (Telegram) session before building the Docker image for portability (as long as you consider this Docker image private at all times). The session file can also be passed in the ```docker run``` command through a Volume. The following instructions assume the former.

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
