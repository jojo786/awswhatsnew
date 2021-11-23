import json
import logging
import os
import time
import boto3
import feedparser
import requests
import twitter
from botocore.client import Config
from html.parser import HTMLParser
from aws_lambda_powertools.utilities import parameters
from slack_sdk import WebClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ssm_provider = parameters.SSMProvider()

stage = os.environ['stage']
print("STAGE: " + stage)

consumer_key = ssm_provider.get("/whatsnew/twitter/"+stage+"/consumer_key", decrypt=True)
consumer_secret = ssm_provider.get("/whatsnew/twitter/"+stage+"/consumer_secret", decrypt=True)
access_token_key = ssm_provider.get("/whatsnew/twitter/"+stage+"s/access_token_key", decrypt=True)
access_token_secret = ssm_provider.get("/whatsnew/twitter/"+stage+"/access_token_secret", decrypt=True)

print("consumer_key: " + consumer_key)

api = twitter.Api(consumer_key=consumer_key,
                  consumer_secret=consumer_secret,
                  access_token_key=access_token_key,
                  access_token_secret=access_token_secret)
    
bot_user_oauth_token = ssm_provider.get("/whatsnew/slack/"+stage+"/bot_user_oauth_token", decrypt=True)
bot_channel_id = ssm_provider.get("/whatsnew/slack/"+stage+"/channel_id", decrypt=True)

client = WebClient(token=bot_user_oauth_token)

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return "".join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


posts_table = boto3.resource("dynamodb", region_name="af-south-1").Table(os.environ["PostsTableName"])

def within(t: time.struct_time, minutes: int) -> bool:
    return abs(time.mktime(time.gmtime()) - time.mktime(t)) <= (minutes * 60)


def already_posted(guid: str) -> bool:
    return "Item" in posts_table.get_item(Key={"guid": guid})

def post_to_twitter(payload, entry):
    api.PostUpdate(
        payload
        + "... "
        + entry.link,
        verify_status_length=False,
    )

def post_to_slack(payload, entry):
    response = client.chat_postMessage(
                    channel=bot_channel_id,
                    text=payload + "\n " + entry.link,
                    icon_emoji=":earth_africa:",
                    username="AWS Whats New in Africa"
                )

def lambda_handler(event, context):
    recency_threshold = int(os.environ['PostRecencyThreshold'])
    payload = ""
    for entry in feedparser.parse("http://aws.amazon.com/new/feed/").entries:
        logger.info(f"Checking {entry.guid} - {entry.title}")
        if ("Cape Town" in entry.title) or ("Cape Town" in entry.description):
            if within(entry.published_parsed, minutes=recency_threshold) and not already_posted(entry.guid):
                logger.info(f"Posting {entry.guid} - {entry.title}")
                payload = entry.title + "\n\n" #+ strip_tags(entry.description)
                try:
                    #length = 300
                    while len(payload) > 249:
                        payload = entry.title + "\n\n" #+ strip_tags(entry.description)
                    logger.info(f"Posting with body length: " + str(len(payload)))
                    logger.info(f"Posting with body: " + payload + "... " + entry.link)                
                    post_to_slack(payload, entry)
                    post_to_twitter(payload, entry)
                    posts_table.put_item(
                        Item={"guid": entry.guid, "title": entry.title, "link": entry.link}
                    )
                except Exception:
                    logger.exception(f"Failed to post")