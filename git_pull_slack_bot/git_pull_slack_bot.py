#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from slacker import Slacker
import websockets
import asyncio
import json
import os
import logging
from logging.handlers import TimedRotatingFileHandler

'''
dependency install

    pip3 install slacker
    pip3 install websockets 
'''

# slack token
TOKEN = ""

LOCAL_GIT_REPO_PREFIX = "/IaC/prod/"

REPO_LST =[
    "terraform-stage",
    "terraform-prod",
    "packer"
    ]

STAGE_GIT_REPO_NM = "terraform-stage"
PROD_GIT_REPO_NM = "terraform-prod"

LOG_DIR = "./"
LOG_FILE_NM = "slack_bot.log"
LOGGING_LOC = "{}{}".format(LOG_DIR, LOG_FILE_NM)


# Create a custom logger
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'

# logging
logger = logging.getLogger()
handler = TimedRotatingFileHandler(LOGGING_LOC, when="midnight")
handler.setFormatter(logging.Formatter(FORMAT))
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())


slack = Slacker(TOKEN)

response = slack.rtm.start()
endpoint = response.body['url']
print("endpoint : {}".format(endpoint))
logger.info("endpoint : {}".format(endpoint))

def get_cmd(target_dir):
    return "git -C {}{} pull".format(LOCAL_GIT_REPO_PREFIX, target_dir)


async def excute_bot():
    ws = await websockets.connect(endpoint)
    while True:
        message_json = await ws.recv()
        m = json.loads(message_json)
        print(m)
        logger.info("msg : {}".format(m))


        if 'subtype' in m.keys() and m['subtype'] == 'bot_message':
            text = m['text']

            for repo in REPO_LST:
                if text.find(repo) != -1:
                    os.system(get_cmd(repo))
                    logger.info("git pull repo : {}".format(repo))
                    break


if __name__ == "__main__":
    for repo in REPO_LST:
        os.system(get_cmd(repo))
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_until_complete(excute_bot())
    asyncio.get_event_loop().run_forever()
