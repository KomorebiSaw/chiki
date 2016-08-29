# coding: utf-8
from .robot import WeRoBot
from .admin import *
from .models import *

__all__ = [
    'WXMsg', 'init_wxmsg',
]

robot = WeRoBot()


class WXMsg(object):

    def __init__(self, app=None):
        self.subscribe_callback = None

    def subscribe_handler(self, callback):
        self.subscribe_callback = callback
        return callback

    @robot.text
    def on_text(self, message):
        msg = Message.objects(keyword=message.content).first()
        if msg:
            reply = msg.reply(message)
            if reply:
                return reply

        default_msg = Message.objects(default=True).first()
        if default_msg:
            return default_msg.reply(message)
        return ''

    @robot.subscribe
    @robot.scan
    def on_subscribe(self, message):
        if self.subscribe_callback:
            res = self.subscribe_callback(message)
            if res:
                return res
        return self.on_text

    @robot.unsubscribe
    def on_unsubscribe(self, message):
        user = um.models.User.get_wechat(mp_openid=message.source)
        if user:
            user.wechat_user.unsubscribe()


def init_wxmsg(app):
    if app.config.get('WEROBOT_TOKEN'):
        return WXMsg(app)
