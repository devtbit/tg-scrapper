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

#### Scraping

Scrape two groups from 2022-01-01 to 2022-03-01 and display every message (skipping media download):

```
inv scrape-groups --targets=MySecretGroup,MyOtherSecretGroup -f 2022-01-01 -t 2022-03-01 -v --skip-media
```
This command will fetch all memebers of the groups (if possible) and all messages and store them in 2 CSV files.

You can also store the messages in a local sqlite database:

```
inv scrape-groups --targets=MySecretGroup -f 2022-02-28 -t 2022-03-01 -e
```

You can specify a custom path with the environment variable `TG_DB_NAME`

#### Uploading to S3

The next command requires AWS CLI with credentials configured (note that account only requires PutObject permissions to the bucket).
Scrape one group from 2022-02-28 to 2022-03-01 and upload everything to a S3 Bucket named MY_BUCKET:

```
inv scrape-groups --targets=MySecretGroup -f 2022-02-28 -t 2022-03-01 -v -u -b MY_BUCKET
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
