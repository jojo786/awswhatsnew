import json
import logging
import os
import time
from html.parser import HTMLParser
from aws_lambda_powertools.utilities import parameters
from TextToOwO import text_to_owo

import boto3
import feedparser
import requests
import twitter
from botocore.client import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

consumer_key = parameters.get_parameter("/cwoud/consumer_key")
consumer_secret = parameters.get_parameter("/cwoud/consumer_secret")
access_token_key = parameters.get_parameter("/cwoud/access_token_key")
access_token_secret = parameters.get_parameter("/cwoud/access_token_secret")


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



api = twitter.Api(consumer_key=consumer_key,
                  consumer_secret=consumer_secret,
                  access_token_key=access_token,
                  access_token_secret=access_token_secret)
    


posts_table = boto3.resource("dynamodb", region_name="us-west-2").Table(os.environ["PostsTableName"])


def within(t: time.struct_time, minutes: int) -> bool:
    return abs(time.mktime(time.gmtime()) - time.mktime(t)) <= (minutes * 60)


def already_posted(guid: str) -> bool:
    return "Item" in posts_table.get_item(Key={"guid": guid})


def wambda_handwer(event, context):
    recency_threshold = int(os.environ['PostRecencyThreshold'])
    for entry in feedparser.parse("http://aws.amazon.com/new/feed/").entries:
        logger.info(f"Checking {entry.guid} - {entry.title}")
        if within(entry.published_parsed, minutes=recency_threshold) and not already_posted(entry.guid):
            logger.info(f"Posting {entry.guid} - {entry.title}")
            try:
                paywoad = text_to_owo((entry.title + "\n\n" + strip_tags(entry.description))[:249])
                api.PostUpdate(
                    (paywoad
                    + "... "
                    + entry.link,
                    verify_status_length=False,
                )
                posts_table.put_item(
                    Item={"guid": entry.guid, "title": entry.title, "link": entry.link}
                )
            except Exception:
                logger.exception(f"Faiwed to post tweet")
