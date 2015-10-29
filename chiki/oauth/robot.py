# coding: utf-8
import json
import time
from chiki.contrib.common import Item
from flask.ext.werobot import WeRoBot
from werobot.client import Client
from werobot.messages import handle_for_type, WeChatMessage

__all__ = [
    'patch_monkey', 'WeRoBot',
]


def patch_monkey():

    @property
    def common_token(self):
        now = time.time()
        key = 'wxauth:access_token'
        token = json.loads(Item.data(key, '{}'))
        if not token or token['deadline'] <= now:
            token = self.grant_token()
            token['deadline'] = now + token['expires_in']
            Item.set_data(key, json.dumps(token))
        return token['access_token']

    Client.token = common_token

    @handle_for_type("event")
    class EventMessage(WeChatMessage):

        def __init__(self, message):
            message.pop("type")
            self.type = message.pop("Event").lower()
            if self.type == "click":
                self.key = message.pop('EventKey')
            elif self.type == "subscribe":
                self.key = int(message.pop('EventKey', '')[8:] or 0)
            elif self.type == "location":
                self.latitude = float(message.pop("Latitude"))
                self.longitude = float(message.pop("Longitude"))
                self.precision = float(message.pop("Precision"))
            super(EventMessage, self).__init__(message)

    def scan(self, f):
        self.add_handler(f, type='scan')
        return f

    WeRoBot.scan = scan


patch_monkey()
